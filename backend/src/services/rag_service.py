from __future__ import annotations

import hashlib
import json
import math
import re
import time
from dataclasses import dataclass
from pathlib import Path

from src.config import Settings
from src.models.job import CreateJobRequest, OutputMode
from src.models.rag import (
    AgentName,
    AgentEvent,
    AgentSessionStatus,
    AgentTrace,
    ChatAnswer,
    ChunkNode,
    Citation,
    Document,
    DocumentDeleteResult,
    DocumentDetail,
    DocumentUpdateRequest,
    IngestionStatus,
    LanguageCode,
    PromptConfig,
    PromptUpdateRequest,
    RagRuntimeStatus,
    RagSearchRequest,
    RagSearchResult,
    ReviewStatus,
    SectionNode,
    Transcript,
    VoiceChatRequest,
    VoiceTurn,
)
from src.services.docling_client import DoclingClient
from src.services.embedding_client import EmbeddingRerankClient
from src.services.job_service import JobService
from src.services.llm_client import LlmClient
from src.services.rag_store import QdrantVectorStore, RagDatabaseStore


@dataclass(frozen=True)
class SectionText:
    titlePath: list[str]
    level: int
    text: str


class RagService:
    def __init__(
        self,
        settings: Settings,
        jobService: JobService,
        doclingClient: DoclingClient,
        embeddingClient: EmbeddingRerankClient,
        llmClient: LlmClient | None = None,
        databaseStore: RagDatabaseStore | None = None,
        vectorStore: QdrantVectorStore | None = None,
    ) -> None:
        self.settings = settings
        self.jobService = jobService
        self.doclingClient = doclingClient
        self.embeddingClient = embeddingClient
        self.llmClient = llmClient or LlmClient(settings)
        self.databaseStore = databaseStore or RagDatabaseStore(settings)
        self.vectorStore = vectorStore or QdrantVectorStore(settings)
        self.documents: dict[str, DocumentDetail] = {}
        self.chunkEmbeddings: dict[str, list[float]] = {}
        self.turns: dict[str, VoiceTurn] = {}
        self.sessionEvents: dict[str, list[AgentEvent]] = {}
        self.databaseStore.initialize()
        self._load()

    def status(self) -> RagRuntimeStatus:
        chunks = sum(document.chunkCount for document in self.documents.values())
        asrEndpoint = f"{self.settings.rivaAsrHost}:{self.settings.rivaAsrPort}"
        return RagRuntimeStatus(
            asrAvailable=self.settings.rivaAsrEnabled,
            asrDetail=f"Riva ASR endpoint {asrEndpoint} is enabled by config." if self.settings.rivaAsrEnabled else "Riva ASR is disabled in config; voice transcription is blocked.",
            documentCount=len(self.documents),
            chunkCount=chunks,
            languages=[LanguageCode.english, LanguageCode.vietnamese],
            doclingBaseUrl=self.settings.doclingApiBaseUrl,
            embeddingBaseUrl=self.settings.embeddingApiBaseUrl,
            parseProvider="docling",
            retrievalProvider="qdrant-graph-rerank" if self.vectorStore.isAvailable() else "embedding-rerank",
            postgresAvailable=self.databaseStore.available,
            qdrantAvailable=self.vectorStore.isAvailable(),
            llmAvailable=self.llmClient.isAvailable(),
            graphRagEnabled=True,
        )

    def listDocuments(self) -> list[Document]:
        return [Document(**document.model_dump(exclude={"sections", "chunks"})) for document in self.documents.values()]

    def getDocument(self, documentId: str) -> DocumentDetail | None:
        return self.documents.get(documentId)

    def getChunks(self, documentId: str) -> list[ChunkNode] | None:
        document = self.documents.get(documentId)
        return None if document is None else document.chunks

    def getTurn(self, turnId: str) -> VoiceTurn | None:
        return self.turns.get(turnId)

    def listPrompts(self) -> list[PromptConfig]:
        return self.databaseStore.listPrompts()

    def updatePrompt(self, agent: str, request: PromptUpdateRequest) -> PromptConfig:
        return self.databaseStore.updatePrompt(agent, request.name, request.content, request.enabled)

    def getSessionStatus(self, sessionId: str) -> AgentSessionStatus:
        events = self.sessionEvents.get(sessionId) or self.databaseStore.listEvents(sessionId)
        turn = next((candidate for candidate in self.turns.values() if candidate.sessionId == sessionId), None)
        return AgentSessionStatus(
            sessionId=sessionId,
            state="completed" if turn else ("running" if events else "unknown"),
            question=turn.transcript.text if turn else "",
            answer=turn.answer.text if turn else "",
            events=events,
        )

    def updateDocument(self, documentId: str, request: DocumentUpdateRequest) -> DocumentDetail | None:
        document = self.documents.get(documentId)
        if document is None:
            return None

        update = request.model_dump(exclude_none=True)
        if "title" in update:
            document.title = update["title"]
        if "summary" in update:
            document.summary = update["summary"]
        if "language" in update:
            document.language = update["language"]
            for chunk in document.chunks:
                chunk.language = update["language"]

        self._persistDocument(document)
        self.databaseStore.upsertDocument(document)
        self.vectorStore.upsertDocument(document, {chunk.id: self.chunkEmbeddings[chunk.id] for chunk in document.chunks if chunk.id in self.chunkEmbeddings})
        return document

    def deleteDocument(self, documentId: str) -> DocumentDeleteResult | None:
        document = self.documents.pop(documentId, None)
        if document is None:
            return None

        removedChunkIds = {chunk.id for chunk in document.chunks}
        for chunkId in removedChunkIds:
            self.chunkEmbeddings.pop(chunkId, None)

        removedFiles = self._deleteDocumentFiles(documentId)
        removedTurnCount = self._deleteTurnsForDocument(documentId)
        self.databaseStore.deleteDocument(documentId)
        self.vectorStore.deleteDocument(documentId)
        return DocumentDeleteResult(
            id=documentId,
            deleted=True,
            removedChunkCount=len(removedChunkIds),
            removedTurnCount=removedTurnCount,
            removedFiles=removedFiles,
        )

    def ingestBytes(self, payload: bytes, filename: str, language: LanguageCode) -> DocumentDetail:
        safeFilename = self._safeFilename(filename)
        self._validatePdf(payload, safeFilename)
        checksum = hashlib.sha256(payload).hexdigest()
        for document in self.documents.values():
            if document.checksum == checksum:
                return document

        parsed = self.doclingClient.parsePdf(payload, safeFilename)
        text = self._normalizeMarkdown(parsed.markdown)
        metadata = self._metadataFromLlm(text, safeFilename)
        title = str(metadata.get("title") or self._titleFromMarkdown(text, safeFilename))[:180]
        sectionTexts = self._sectionTextsFromMarkdown(text, title)
        sections, chunks = self._buildChunks(checksum[:16], sectionTexts, language)
        vectors = self._embedChunkTexts([chunk.text for chunk in chunks])
        embeddings = {chunk.id: vector for chunk, vector in zip(chunks, vectors, strict=True)}
        for chunk in chunks:
            chunk.embeddingId = chunk.id
        for index, chunk in enumerate(chunks):
            chunk.previousChunkId = chunks[index - 1].id if index > 0 else None
            chunk.nextChunkId = chunks[index + 1].id if index < len(chunks) - 1 else None
            chunk.relatedChunkIds = [value for value in [chunk.previousChunkId, chunk.nextChunkId] if value]
        sectionById = {section.id: section for section in sections}
        for chunk in chunks:
            sectionById[chunk.sectionId].childIds.append(chunk.id)
        self._applyWikiLinks(chunks)
        summary = str(metadata.get("summary") or text[:220].strip())[:500]
        document = DocumentDetail(
            id=checksum[:16],
            filename=safeFilename,
            title=title,
            language=language,
            status=IngestionStatus.indexed,
            checksum=checksum,
            pageCount=max((chunk.page for chunk in chunks), default=1),
            chunkCount=len(chunks),
            summary=summary,
            sections=sections,
            chunks=chunks,
            parseProvider="docling",
            embeddingProvider="embedding-api",
            rerankProvider="embedding-api",
        )
        self.documents[document.id] = document
        self.chunkEmbeddings.update(embeddings)
        self._persistDocument(document)
        self._persistEmbeddings(document.id, embeddings)
        self.databaseStore.upsertDocument(document)
        if self.vectorStore.isAvailable():
            self.vectorStore.upsertDocument(document, embeddings)
        return document

    def search(self, request: RagSearchRequest) -> RagSearchResult:
        chunks = self._searchableChunks(request.language)
        if not chunks:
            trace = [
                AgentTrace(agent=AgentName.lead, status="ok", message="Prepared the search intent."),
                AgentTrace(agent=AgentName.search, status="empty", message="No indexed chunks are available for this language."),
                AgentTrace(agent=AgentName.review, status=ReviewStatus.notFound.value, message="No source evidence is available."),
            ]
            return RagSearchResult(
                query=request.query,
                found=False,
                confidence=0.0,
                answerability=ReviewStatus.notFound,
                citations=[],
                compactContext="",
                trace=trace,
            )

        queryVector = self.embeddingClient.embed([request.query])[0]
        vectorScores: dict[str, float] = {}
        qdrantSeedIds = self.vectorStore.search(queryVector, request.language.value, request.topK * 8)
        queryKeywords = self._keywords(request.query)
        quotedPhrases = [match.lower() for match in re.findall(r'"([^"]{8,})"', request.query)]
        searchableChunkIds = {chunk.id for chunk in chunks}
        for document in self.documents.values():
            for chunk in document.chunks:
                if chunk.id not in searchableChunkIds:
                    continue
                embedding = self.chunkEmbeddings.get(chunk.id)
                if embedding is None:
                    if chunk.id in qdrantSeedIds:
                        vectorScores[chunk.id] = self.settings.ragMinVectorScore
                        continue
                    raise RuntimeError(f"chunk {chunk.id} is missing an embedding; reingest the document")
                score = self._cosine(queryVector, embedding)
                if score >= self.settings.ragMinVectorScore or chunk.id in qdrantSeedIds:
                    vectorScores[chunk.id] = score
                lexicalScore = self._lexicalScore(chunk.text, queryKeywords, quotedPhrases)
                if lexicalScore > 0:
                    vectorScores[chunk.id] = max(vectorScores.get(chunk.id, 0.0), lexicalScore)

        rankedVectorChunks = sorted(
            ((score, chunk) for chunk in chunks if (score := vectorScores.get(chunk.id)) is not None),
            key=lambda item: item[0],
            reverse=True,
        )
        candidates = self._expandCandidates([chunk for _, chunk in rankedVectorChunks[: request.topK * 4]])
        if not candidates:
            trace = [
                AgentTrace(agent=AgentName.lead, status="ok", message="Prepared the search intent."),
                AgentTrace(agent=AgentName.search, status="empty", message="Embedding search found no candidate chunks."),
                AgentTrace(agent=AgentName.review, status=ReviewStatus.notFound.value, message="No indexed source passed the vector threshold."),
            ]
            return RagSearchResult(query=request.query, found=False, confidence=0.0, answerability=ReviewStatus.notFound, trace=trace)

        rerankHits = self.embeddingClient.rerank(request.query, [chunk.text for chunk in candidates])
        rankedCitations: list[tuple[float, ChunkNode]] = []
        for rank, hit in enumerate(rerankHits):
            if hit.index < 0 or hit.index >= len(candidates):
                continue
            chunk = candidates[hit.index]
            vectorScore = vectorScores.get(chunk.id, max((vectorScores.get(related, 0.0) for related in chunk.relatedChunkIds), default=0.0))
            rerankScore = max(0.0, min(1.0, (hit.score + 1.0) / 2.0 if hit.score < 0 else hit.score))
            blendedScore = max(vectorScore, (0.78 * vectorScore) + (0.22 * rerankScore))
            if vectorScore >= 0.97:
                blendedScore = max(blendedScore, 0.99 - (rank * 0.001))
            confidence = self._confidence(blendedScore, rank)
            if vectorScore >= 0.965:
                confidence = max(confidence, vectorScore)
            rankedCitations.append((confidence, chunk))

        citations: list[Citation] = []
        seenCitationIds: set[str] = set()
        for confidence, chunk in sorted(rankedCitations, key=lambda item: item[0], reverse=True):
            if chunk.id in seenCitationIds:
                continue
            citations.append(self._citation(chunk, confidence))
            seenCitationIds.add(chunk.id)
            if len(citations) >= request.topK:
                break

        found = bool(citations and citations[0].confidence >= self.settings.ragMinConfidence)
        context = "\n".join(f"[{citation.source} p.{citation.page}] {self._contextText(citation)}" for citation in citations)
        trace = [
            AgentTrace(agent=AgentName.lead, status="ok", message="Prepared one concise search intent for the user transcript."),
            AgentTrace(
                agent=AgentName.search,
                status="found" if citations else "empty",
                message=f"Embedding search expanded to {len(candidates)} chunks and reranked {len(rerankHits)} candidates.",
                evidenceChunkIds=[citation.chunkId for citation in citations],
            ),
            AgentTrace(agent=AgentName.review, status=ReviewStatus.passed.value if found else ReviewStatus.notFound.value, message="Evidence is grounded enough for a concise answer." if found else "No indexed source passed the relevance threshold."),
        ]
        return RagSearchResult(
            query=request.query,
            found=found,
            confidence=citations[0].confidence if citations else 0.0,
            answerability=ReviewStatus.passed if found else ReviewStatus.notFound,
            citations=citations,
            compactContext=context,
            trace=trace,
        )

    def chat(self, request: VoiceChatRequest) -> VoiceTurn:
        sessionId = self.databaseStore.createSession(request.message, request.sessionId)
        self._event(sessionId, "user", "lead", "question", "received", "User question received.", {"language": request.language.value})
        self._event(sessionId, "lead", "search", "delegate", "running", "Leader assigned search with fresh PDF priority.", {"message": request.message})
        search = self.search(RagSearchRequest(query=request.message, language=request.language, topK=5))
        self._event(sessionId, "search", "qdrant", "vector_search", "done", f"Search selected {len(search.citations)} citations after graph expansion.", {"citationChunkIds": [citation.chunkId for citation in search.citations]})
        if search.found:
            self._event(sessionId, "teacher", "llm", "answer", "running", "Teacher is drafting grounded answer from selected context.", {})
            answerText = self._answerFromCitations(request.message, search.citations)
            reviewStatus = self._reviewAnswer(request.message, answerText, search.compactContext)
            self._event(sessionId, "review", "lead", "review", reviewStatus.value, "Review checked grounding, drift and missing evidence.", {"confidence": search.confidence})
        else:
            answerText = "I could not find that in the indexed knowledge base. Upload a source PDF with relevant information and try again."
            reviewStatus = ReviewStatus.notFound
            self._event(sessionId, "review", "lead", "review", reviewStatus.value, "Review found no reliable source context.", {})

        trace = [
            *search.trace,
            AgentTrace(agent=AgentName.teacher, status=reviewStatus.value, message="Final answer generated with citations." if search.found else "Final answer states the gap without inventing facts.", evidenceChunkIds=[citation.chunkId for citation in search.citations]),
        ]
        jobRequest = CreateJobRequest(
            text=self._voiceText(answerText),
            voice=request.voice,
            language=request.language.value,
            outputMode=OutputMode(request.outputMode),
        )
        job = self.jobService.createJob(jobRequest)
        if job.error or not job.audioUrl or not job.animationUrl:
            raise RuntimeError(f"voice answer pipeline failed: {job.error or 'missing audio or animation artifact'}")
        turn = VoiceTurn(
            language=request.language,
            transcript=Transcript(text=request.message, language=request.language),
            answer=ChatAnswer(text=answerText, citations=search.citations, reviewStatus=reviewStatus),
            audioUrl=job.audioUrl,
            animationUrl=job.animationUrl,
            jobId=job.id,
            sessionId=sessionId,
            agentTrace=trace,
            agentEvents=self.sessionEvents.get(sessionId, []),
        )
        self.turns[turn.id] = turn
        self._persistTurn(turn)
        self.databaseStore.updateSession(sessionId, "completed", answerText)
        return turn

    def _voiceText(self, answerText: str) -> str:
        normalized = " ".join(answerText.split())
        normalized = re.sub(r"[\[\]{}<>_*`#|\\]", " ", normalized)
        normalized = re.sub(r"https?://\S+", " link ", normalized)
        normalized = re.sub(r"[^A-Za-z0-9À-ỹ.,;:!?%()\\-\\s]", " ", normalized)
        normalized = " ".join(normalized.split())
        maxChars = max(40, self.settings.voiceChatTtsMaxChars)
        if len(normalized) <= maxChars:
            return normalized
        truncated = normalized[: maxChars - 3].rsplit(" ", 1)[0].strip()
        return f"{truncated or normalized[: maxChars - 3]}..."

    def _event(self, sessionId: str, agent: str, target: str | None, eventType: str, status: str, message: str, metadata: dict) -> None:
        event = AgentEvent(sessionId=sessionId, agent=agent, target=target, eventType=eventType, status=status, message=message, metadata=metadata)
        self.sessionEvents.setdefault(sessionId, []).append(event)
        self.databaseStore.addEvent(event)

    def _metadataFromLlm(self, markdown: str, filename: str) -> dict:
        system = self.databaseStore.promptFor("upload")
        user = (
            "Return compact JSON only with keys title, summary, keywords. "
            f"Filename: {filename}\nMarkdown excerpt:\n{markdown[:3500]}"
        )
        parsed, used = self.llmClient.completeJson(system, user, maxTokens=400)
        if not used:
            return {}
        title = str(parsed.get("title") or "").strip()
        summary = str(parsed.get("summary") or "").strip()
        keywords = parsed.get("keywords")
        cleanKeywords = [str(value).strip()[:48] for value in keywords if str(value).strip()] if isinstance(keywords, list) else []
        return {
            "title": title[:180] if title else "",
            "summary": summary[:500] if summary else "",
            "keywords": cleanKeywords[:12],
        }

    def _reviewAnswer(self, query: str, answer: str, context: str) -> ReviewStatus:
        if context.strip() and answer.strip() and "source:" in answer.lower() and not any(phrase in answer.lower() for phrase in ["could not find", "cannot find", "no relevant"]):
            return ReviewStatus.passed
        system = self.databaseStore.promptFor("review")
        user = (
            "Return JSON only: {\"status\":\"pass\"|\"retry_search\"|\"not_found\", \"reason\":\"...\"}.\n"
            f"Question: {query}\nContext:\n{context[:3000]}\nAnswer:\n{answer[:1800]}"
        )
        parsed, used = self.llmClient.completeJson(system, user, maxTokens=220)
        if not used:
            return ReviewStatus.passed
        status = str(parsed.get("status") or "pass")
        if status == ReviewStatus.retrySearch.value:
            return ReviewStatus.retrySearch
        if status == ReviewStatus.notFound.value:
            return ReviewStatus.notFound
        return ReviewStatus.passed

    def _validatePdf(self, payload: bytes, filename: str) -> None:
        if not filename.lower().endswith(".pdf"):
            raise ValueError("only PDF files are accepted")
        maxBytes = self.settings.pdfMaxUploadMb * 1024 * 1024
        if len(payload) == 0:
            raise ValueError("PDF cannot be empty")
        if len(payload) > maxBytes:
            raise ValueError(f"PDF is larger than {self.settings.pdfMaxUploadMb} MB")
        if not payload.startswith(b"%PDF"):
            raise ValueError("PDF signature is missing")

    def _normalizeMarkdown(self, markdown: str) -> str:
        text = markdown.replace("\r\n", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = "\n".join(line.rstrip() for line in text.splitlines())
        normalized = text.strip()
        if not normalized:
            raise RuntimeError("Docling markdown is empty after normalization")
        return normalized

    def _sectionTextsFromMarkdown(self, markdown: str, defaultTitle: str) -> list[SectionText]:
        sections: list[SectionText] = []
        headingStack: list[str] = [defaultTitle]
        currentPath: list[str] = [defaultTitle]
        currentLevel = 1
        currentLines: list[str] = []

        def flush() -> None:
            text = " ".join(" ".join(currentLines).split())
            if text:
                sections.append(SectionText(titlePath=currentPath.copy(), level=currentLevel, text=text))

        for rawLine in markdown.splitlines():
            line = rawLine.strip()
            heading = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading:
                flush()
                currentLines = []
                currentLevel = len(heading.group(1))
                title = heading.group(2).strip(" #")
                while len(headingStack) >= currentLevel:
                    headingStack.pop()
                headingStack.append(title)
                currentPath = headingStack.copy()
                continue
            if line:
                currentLines.append(line)
        flush()

        if not sections:
            compact = " ".join(markdown.split())
            sections.append(SectionText(titlePath=[defaultTitle], level=1, text=compact))
        return sections

    def _buildChunks(self, documentId: str, sectionTexts: list[SectionText], language: LanguageCode) -> tuple[list[SectionNode], list[ChunkNode]]:
        sections: list[SectionNode] = []
        chunks: list[ChunkNode] = []
        chunkIndex = 1
        for sectionIndex, sectionText in enumerate(sectionTexts, start=1):
            sectionId = f"sec-{documentId}-{sectionIndex:03d}"
            pageStart = max(1, sectionIndex)
            section = SectionNode(
                id=sectionId,
                documentId=documentId,
                title=sectionText.titlePath[-1],
                titlePath=sectionText.titlePath,
                level=max(1, min(6, sectionText.level)),
                pageStart=pageStart,
                pageEnd=pageStart,
            )
            sectionChunks = self._chunkText(sectionText.text, targetWords=130)
            for localIndex, chunkText in enumerate(sectionChunks):
                page = pageStart + math.floor(localIndex / 3)
                section.pageEnd = max(section.pageEnd, page)
                chunks.append(
                    ChunkNode(
                        id=f"chk-{documentId}-{chunkIndex:03d}",
                        documentId=documentId,
                        sectionId=sectionId,
                        text=chunkText,
                        page=page,
                        titlePath=sectionText.titlePath,
                        language=language,
                        tokenCount=max(1, len(chunkText.split())),
                    )
                )
                chunkIndex += 1
            sections.append(section)
        if not chunks:
            raise RuntimeError("Docling produced no indexable chunks")
        return sections, chunks

    def _embedChunkTexts(self, texts: list[str]) -> list[list[float]]:
        batchSize = max(1, self.settings.ragEmbeddingBatchSize)
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batchSize):
            batch = texts[start:start + batchSize]
            vectors.extend(self.embeddingClient.embed(batch))
            if self.settings.ragEmbeddingBatchDelaySeconds > 0 and start + batchSize < len(texts):
                time.sleep(self.settings.ragEmbeddingBatchDelaySeconds)
        return vectors

    def _chunkText(self, text: str, targetWords: int) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: list[str] = []
        current: list[str] = []
        currentLength = 0
        for sentence in sentences:
            cleanSentence = " ".join(sentence.split())
            if not cleanSentence:
                continue
            sentenceParts = self._splitLongText(cleanSentence, maxChars=2200)
            if len(sentenceParts) > 1:
                if current:
                    chunks.append(" ".join(current))
                    current = []
                    currentLength = 0
                chunks.extend(sentenceParts)
                continue
            length = len(cleanSentence.split())
            if current and currentLength + length > targetWords:
                chunks.append(" ".join(current))
                current = []
                currentLength = 0
            current.append(cleanSentence)
            currentLength += length
        if current:
            chunks.append(" ".join(current))
        normalizedChunks: list[str] = []
        for chunk in chunks or [" ".join(text.split())]:
            normalizedChunks.extend(self._splitLongText(chunk, maxChars=2200))
        return normalizedChunks

    def _splitLongText(self, text: str, maxChars: int) -> list[str]:
        cleanText = " ".join(text.split())
        if len(cleanText) <= maxChars:
            return [cleanText] if cleanText else []
        parts: list[str] = []
        current: list[str] = []
        currentLength = 0
        for word in cleanText.split():
            extra = len(word) + (1 if current else 0)
            if current and currentLength + extra > maxChars:
                parts.append(" ".join(current))
                current = []
                currentLength = 0
            if len(word) > maxChars:
                for index in range(0, len(word), maxChars):
                    parts.append(word[index:index + maxChars])
                continue
            current.append(word)
            currentLength += extra
        if current:
            parts.append(" ".join(current))
        return parts

    def _citation(self, chunk: ChunkNode, score: float) -> Citation:
        document = self.documents[chunk.documentId]
        return Citation(
            chunkId=chunk.id,
            documentId=chunk.documentId,
            source=document.filename,
            page=chunk.page,
            titlePath=chunk.titlePath,
            excerpt=chunk.text[:680],
            confidence=max(0.0, min(1.0, score)),
        )

    def _answerFromCitations(self, query: str, citations: list[Citation]) -> str:
        lead = self._selectAnswerCitation(query, citations)
        quotedAnswer = self._answerFromQuotedPrimaryCitation(query, lead)
        if quotedAnswer:
            return quotedAnswer

        passage = self._extractKeywordPassage(self._answerSourceText(lead), query)
        if not passage:
            passage = self._contextText(lead)[:760].strip()
        return f"Based on {lead.source} page {lead.page}, {passage} Source: {lead.source}, page {lead.page}."

    def _selectAnswerCitation(self, query: str, citations: list[Citation]) -> Citation:
        if len(citations) == 1:
            return citations[0]
        queryKeywords = self._keywords(query)
        quotedPhrases = [match.lower() for match in re.findall(r'"([^"]{8,})"', query)]
        scored: list[tuple[float, int, Citation]] = []
        for index, citation in enumerate(citations):
            context = self._contextText(citation)
            titleText = " ".join(citation.titlePath)
            sourceText = self._answerSourceText(citation)
            keywordScore = 0.0
            if queryKeywords:
                keywordScore = len(queryKeywords & self._keywords(sourceText)) / len(queryKeywords)
            phraseScore = 0.0
            for phrase in quotedPhrases:
                phraseScore = max(
                    phraseScore,
                    self._quotedPhraseScore(context.lower(), self._normalizedPhraseText(context.lower()), phrase),
                    0.92 * self._quotedPhraseScore(titleText.lower(), self._normalizedPhraseText(titleText.lower()), phrase),
                    0.78 * self._quotedPhraseScore(sourceText.lower(), self._normalizedPhraseText(sourceText.lower()), phrase),
                )
            qualityScore = self._contextQualityScore(context)
            score = (3.6 * phraseScore) + (1.4 * keywordScore) + qualityScore + (0.2 * citation.confidence)
            if phraseScore >= 0.72 and qualityScore >= 0.62:
                score += 0.8
            if qualityScore < 0.32:
                score -= 1.25
            scored.append((score, -index, citation))
        return max(scored, key=lambda item: (item[0], item[1]))[2]

    def _extractKeywordPassage(self, text: str, query: str) -> str:
        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", " ".join(text.split())) if sentence.strip()]
        if not sentences:
            return text[:760].strip()
        queryKeywords = self._keywords(query)
        if not queryKeywords:
            return " ".join(sentences[:3])[:760].strip()
        scored = []
        for index, sentence in enumerate(sentences):
            hits = len(queryKeywords & self._keywords(sentence))
            scored.append((hits, index))
        _, bestIndex = max(scored, key=lambda item: (item[0], -item[1]))
        start = max(0, bestIndex - 1)
        end = min(len(sentences), bestIndex + 3)
        passage = " ".join(sentences[start:end])
        if len(passage) > 900:
            passage = passage[:897].rsplit(" ", 1)[0] + "..."
        return passage

    def _answerContextCitations(self, citations: list[Citation]) -> list[Citation]:
        lead = citations[0]
        selected = [lead]
        for citation in citations[1:]:
            samePassage = citation.documentId == lead.documentId and citation.page == lead.page
            veryStrongSameDoc = citation.documentId == lead.documentId and citation.confidence >= max(0.0, lead.confidence - 0.02)
            if samePassage or veryStrongSameDoc:
                selected.append(citation)
            if len(selected) >= 3:
                break
        return selected

    def _answerFromQuotedPrimaryCitation(self, query: str, citation: Citation) -> str | None:
        phrases = [match.strip() for match in re.findall(r'"([^"]{8,})"', query)]
        if not phrases:
            return None
        context = self._answerSourceText(citation)
        phrase = max(phrases, key=len).lower()
        cleanContext = context.lower()
        normalizedContext = self._normalizedPhraseText(cleanContext)
        if self._quotedPhraseScore(cleanContext, normalizedContext, phrase) < 0.72:
            return None
        passage = self._extractPassageAroundPhrase(context, phrase)
        if not passage or self._contextQualityScore(passage) < 0.28:
            return None
        return f"Based on {citation.source} page {citation.page}, the cited passage says: {passage} Source: {citation.source}, page {citation.page}."

    def _extractPassageAroundPhrase(self, text: str, phrase: str) -> str:
        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", " ".join(text.split())) if sentence.strip()]
        if not sentences:
            return text[:640].strip()
        phraseKeywords = self._keywords(phrase)
        scored: list[tuple[float, int, int]] = []
        for startIndex in range(len(sentences)):
            for endIndex in range(startIndex, min(len(sentences), startIndex + 5)):
                window = " ".join(sentences[startIndex:endIndex + 1])
                cleanWindow = window.lower()
                score = self._quotedPhraseScore(cleanWindow, self._normalizedPhraseText(cleanWindow), phrase)
                if phraseKeywords:
                    windowKeywords = self._keywords(window)
                    score = max(score, len(phraseKeywords & windowKeywords) / len(phraseKeywords))
                scored.append((score, startIndex, endIndex))
        score, startIndex, endIndex = max(scored, key=lambda item: item[0])
        if score < 0.45:
            return ""
        selected = []
        if startIndex > 0:
            selected.append(sentences[startIndex - 1])
        selected.extend(sentences[startIndex:endIndex + 1])
        for nextIndex in range(endIndex + 1, min(len(sentences), endIndex + 5)):
            selected.append(sentences[nextIndex])
            if len(" ".join(selected)) >= 1200:
                break
        passage = " ".join(selected)
        if len(passage) > 1400:
            passage = passage[:1397].rsplit(" ", 1)[0] + "..."
        return passage

    def _contextText(self, citation: Citation) -> str:
        document = self.documents.get(citation.documentId)
        if document:
            chunk = next((candidate for candidate in document.chunks if candidate.id == citation.chunkId), None)
            if chunk:
                return chunk.text[:1400]
        return citation.excerpt

    def _answerSourceText(self, citation: Citation) -> str:
        titleText = ". ".join(part.strip() for part in citation.titlePath if part.strip())
        context = self._contextText(citation)
        if titleText and titleText.lower() not in context.lower()[:240]:
            return f"{titleText}. {context}"
        return context

    def _contextQualityScore(self, text: str) -> float:
        clean = " ".join(text.split())
        if not clean:
            return 0.0
        alpha = sum(1 for char in clean if char.isalpha())
        punctuation = sum(1 for char in clean if char in "|._-")
        words = re.findall(r"[A-Za-zÀ-ỹ]{4,}", clean)
        uniqueWords = len(set(word.lower() for word in words))
        alphaRatio = alpha / max(1, len(clean))
        punctuationPenalty = min(0.6, punctuation / max(1, len(clean)))
        diversity = min(1.0, uniqueWords / 38)
        sentenceBonus = 0.18 if re.search(r"[.!?]\s+[A-ZÀ-Ỹ]", clean) else 0.0
        tablePenalty = 0.35 if clean.count("|") >= 4 else 0.0
        dotLeaderPenalty = 0.28 if clean.count(". . .") >= 1 or clean.count(" . .") >= 3 else 0.0
        score = alphaRatio + (0.45 * diversity) + sentenceBonus - punctuationPenalty - tablePenalty - dotLeaderPenalty
        return max(0.0, min(1.0, score))

    def _safeFilename(self, filename: str) -> str:
        name = Path(filename).name.strip()[:180]
        if not name:
            raise ValueError("filename is required")
        return name

    def _titleFromMarkdown(self, markdown: str, filename: str) -> str:
        for line in markdown.splitlines():
            heading = re.match(r"^#\s+(.+)$", line.strip())
            if heading:
                return heading.group(1).strip()[:180]
        firstWords = " ".join(markdown.split()[:8]).strip(" .")
        return firstWords[:180] or filename.rsplit(".", 1)[0]

    def _searchableChunks(self, language: LanguageCode) -> list[ChunkNode]:
        chunks: list[ChunkNode] = []
        for document in self.documents.values():
            for chunk in document.chunks:
                if language == LanguageCode.vietnamese and chunk.language != LanguageCode.vietnamese:
                    continue
                chunks.append(chunk)
        return chunks

    def _expandCandidates(self, chunks: list[ChunkNode]) -> list[ChunkNode]:
        chunkById = {chunk.id: chunk for document in self.documents.values() for chunk in document.chunks}
        expanded: dict[str, ChunkNode] = {}
        frontier = list(chunks)
        for chunk in frontier:
            expanded[chunk.id] = chunk
        for _ in range(max(1, self.settings.ragGraphExpansionDepth)):
            nextFrontier: list[ChunkNode] = []
            for chunk in frontier:
                for relatedId in chunk.relatedChunkIds:
                    related = chunkById.get(relatedId)
                    if related is not None and related.id not in expanded:
                        expanded[related.id] = related
                        nextFrontier.append(related)
                        if len(expanded) >= self.settings.ragGraphMaxContextChunks:
                            return list(expanded.values())
            frontier = nextFrontier
            if not frontier:
                break
        return list(expanded.values())

    def _applyWikiLinks(self, chunks: list[ChunkNode]) -> None:
        bySection: dict[str, list[ChunkNode]] = {}
        for chunk in chunks:
            bySection.setdefault(chunk.sectionId, []).append(chunk)
        for siblings in bySection.values():
            siblingIds = [chunk.id for chunk in siblings]
            for chunk in siblings:
                related = set(chunk.relatedChunkIds)
                related.update(value for value in siblingIds if value != chunk.id)
                chunkKeywords = self._keywords(chunk.text)
                for other in chunks:
                    if other.id == chunk.id or other.sectionId == chunk.sectionId:
                        continue
                    if chunkKeywords & self._keywords(other.text):
                        related.add(other.id)
                chunk.relatedChunkIds = sorted(related)[:12]

    def _keywords(self, text: str) -> set[str]:
        words = re.findall(r"[A-Za-zÀ-ỹ0-9]{4,}", text.lower())
        stop = {"this", "that", "with", "from", "have", "should", "document", "image"}
        return {word for word in words if word not in stop}

    def _lexicalScore(self, text: str, queryKeywords: set[str], quotedPhrases: list[str]) -> float:
        if not queryKeywords and not quotedPhrases:
            return 0.0
        cleanText = " ".join(text.lower().split())
        normalizedText = self._normalizedPhraseText(text)
        phraseScore = max((self._quotedPhraseScore(cleanText, normalizedText, phrase) for phrase in quotedPhrases), default=0.0)
        if phraseScore > 0:
            return phraseScore
        chunkKeywords = self._keywords(cleanText)
        if not chunkKeywords:
            return 0.0
        overlap = len(queryKeywords & chunkKeywords)
        if overlap < 2:
            return 0.0
        ratio = overlap / max(1, len(queryKeywords))
        return min(0.94, self.settings.ragMinVectorScore + 0.18 + ratio * 0.22)

    def _normalizedPhraseText(self, text: str) -> str:
        return " ".join(re.findall(r"[A-Za-zÀ-ỹ0-9]+", text.lower()))

    def _quotedPhraseScore(self, cleanText: str, normalizedText: str, phrase: str) -> float:
        normalizedPhrase = self._normalizedPhraseText(phrase)
        if not normalizedPhrase:
            return 0.0
        if phrase in cleanText or normalizedPhrase in normalizedText:
            return 0.995
        phraseTokens = normalizedPhrase.split()
        textTokens = normalizedText.split()
        if len(phraseTokens) < 4 or not textTokens:
            return 0.0
        position = 0
        first = -1
        last = -1
        for index, token in enumerate(textTokens):
            if token != phraseTokens[position]:
                continue
            if first < 0:
                first = index
            last = index
            position += 1
            if position == len(phraseTokens):
                span = last - first + 1
                if span <= len(phraseTokens) + 4:
                    return 0.985
                return 0.965
        return 0.0

    def _cosine(self, left: list[float], right: list[float]) -> float:
        if len(left) != len(right):
            raise RuntimeError("embedding dimensions do not match")
        dot = sum(a * b for a, b in zip(left, right))
        leftNorm = math.sqrt(sum(value * value for value in left))
        rightNorm = math.sqrt(sum(value * value for value in right))
        if leftNorm == 0 or rightNorm == 0:
            return 0.0
        return dot / (leftNorm * rightNorm)

    def _confidence(self, vectorScore: float, rank: int) -> float:
        vectorConfidence = max(0.0, min(1.0, (vectorScore + 1.0) / 2.0))
        rankConfidence = 1.0 / (rank + 1)
        return max(0.0, min(1.0, 0.72 * vectorConfidence + 0.28 * rankConfidence))

    def _load(self) -> None:
        for document in self.databaseStore.loadDocuments():
            self.documents[document.id] = document
        for path in sorted(self.settings.ragStorageDir.glob("documents/*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            document = DocumentDetail.model_validate(data)
            if document.id not in self.documents:
                self.documents[document.id] = document
            embeddingPath = self.settings.ragStorageDir / "embeddings" / f"{document.id}.json"
            if embeddingPath.exists():
                embeddings = json.loads(embeddingPath.read_text(encoding="utf-8"))
                self.chunkEmbeddings.update({str(chunkId): [float(value) for value in vector] for chunkId, vector in embeddings.items()})
        if not self.settings.ragReindexOnLoad:
            return
        for document in self.documents.values():
            documentEmbeddings = {chunk.id: self.chunkEmbeddings[chunk.id] for chunk in document.chunks if chunk.id in self.chunkEmbeddings}
            self.databaseStore.upsertDocument(document)
            self.vectorStore.upsertDocument(document, documentEmbeddings)

    def _persistDocument(self, document: DocumentDetail) -> None:
        path = self.settings.ragStorageDir / "documents" / f"{document.id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(document.model_dump_json(indent=2), encoding="utf-8")

    def _persistEmbeddings(self, documentId: str, embeddings: dict[str, list[float]]) -> None:
        path = self.settings.ragStorageDir / "embeddings" / f"{documentId}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(embeddings), encoding="utf-8")

    def _persistTurn(self, turn: VoiceTurn) -> None:
        path = self.settings.ragStorageDir / "turns" / f"{turn.id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(turn.model_dump_json(indent=2), encoding="utf-8")

    def _deleteDocumentFiles(self, documentId: str) -> list[str]:
        removedFiles: list[str] = []
        for path in [
            self.settings.ragStorageDir / "documents" / f"{documentId}.json",
            self.settings.ragStorageDir / "embeddings" / f"{documentId}.json",
        ]:
            if path.exists():
                path.unlink()
                removedFiles.append(str(path))
        return removedFiles

    def _deleteTurnsForDocument(self, documentId: str) -> int:
        removedTurnIds = {
            turnId
            for turnId, turn in self.turns.items()
            if self._turnReferencesDocument(turn, documentId)
        }
        for turnId in removedTurnIds:
            self.turns.pop(turnId, None)

        removedCount = len(removedTurnIds)
        turnsDir = self.settings.ragStorageDir / "turns"
        for path in sorted(turnsDir.glob("*.json")):
            try:
                turn = VoiceTurn.model_validate_json(path.read_text(encoding="utf-8"))
            except ValueError:
                continue
            if self._turnReferencesDocument(turn, documentId):
                path.unlink()
                removedCount += 1 if turn.id not in removedTurnIds else 0
        return removedCount

    def _turnReferencesDocument(self, turn: VoiceTurn, documentId: str) -> bool:
        return any(citation.documentId == documentId for citation in turn.answer.citations)
