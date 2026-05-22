from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from src.config import Settings
from src.models.job import CreateJobRequest, OutputMode
from src.models.rag import (
    AgentName,
    AgentTrace,
    ChatAnswer,
    ChunkNode,
    Citation,
    Document,
    DocumentDetail,
    IngestionStatus,
    LanguageCode,
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
    ) -> None:
        self.settings = settings
        self.jobService = jobService
        self.doclingClient = doclingClient
        self.embeddingClient = embeddingClient
        self.documents: dict[str, DocumentDetail] = {}
        self.chunkEmbeddings: dict[str, list[float]] = {}
        self.turns: dict[str, VoiceTurn] = {}
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
            retrievalProvider="embedding-rerank",
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

    def ingestBytes(self, payload: bytes, filename: str, language: LanguageCode) -> DocumentDetail:
        safeFilename = self._safeFilename(filename)
        self._validatePdf(payload, safeFilename)
        checksum = hashlib.sha256(payload).hexdigest()
        for document in self.documents.values():
            if document.checksum == checksum:
                return document

        parsed = self.doclingClient.parsePdf(payload, safeFilename)
        text = self._normalizeMarkdown(parsed.markdown)
        title = self._titleFromMarkdown(text, safeFilename)
        sectionTexts = self._sectionTextsFromMarkdown(text, title)
        sections, chunks = self._buildChunks(checksum[:16], sectionTexts, language)
        vectors = self.embeddingClient.embed([chunk.text for chunk in chunks])
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
        summary = text[:220].strip()
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
        for document in self.documents.values():
            for chunk in document.chunks:
                if chunk not in chunks:
                    continue
                embedding = self.chunkEmbeddings.get(chunk.id)
                if embedding is None:
                    raise RuntimeError(f"chunk {chunk.id} is missing an embedding; reingest the document")
                score = self._cosine(queryVector, embedding)
                if score >= self.settings.ragMinVectorScore:
                    vectorScores[chunk.id] = score

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
        citations: list[Citation] = []
        for rank, hit in enumerate(rerankHits):
            if hit.index < 0 or hit.index >= len(candidates):
                continue
            chunk = candidates[hit.index]
            vectorScore = vectorScores.get(chunk.id, max((vectorScores.get(related, 0.0) for related in chunk.relatedChunkIds), default=0.0))
            confidence = self._confidence(vectorScore, rank)
            citations.append(self._citation(chunk, confidence))
            if len(citations) >= request.topK:
                break

        found = bool(citations and citations[0].confidence >= self.settings.ragMinConfidence)
        context = "\n".join(f"[{citation.source} p.{citation.page}] {citation.excerpt}" for citation in citations)
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
        search = self.search(RagSearchRequest(query=request.message, language=request.language, topK=5))
        if search.found:
            answerText = self._answerFromCitations(request.message, search.citations)
            reviewStatus = ReviewStatus.passed
        else:
            answerText = "I could not find that in the indexed knowledge base. Upload a source PDF with relevant information and try again."
            reviewStatus = ReviewStatus.notFound

        trace = [
            *search.trace,
            AgentTrace(agent=AgentName.teacher, status=reviewStatus.value, message="Final answer generated with citations." if search.found else "Final answer states the gap without inventing facts.", evidenceChunkIds=[citation.chunkId for citation in search.citations]),
        ]
        job = self.jobService.createJob(
            CreateJobRequest(
                text=answerText,
                voice=request.voice,
                language=request.language.value,
                outputMode=OutputMode(request.outputMode),
            )
        )
        if job.error or not job.audioUrl or not job.animationUrl:
            raise RuntimeError(f"voice answer pipeline failed: {job.error or 'missing audio or animation artifact'}")
        turn = VoiceTurn(
            language=request.language,
            transcript=Transcript(text=request.message, language=request.language),
            answer=ChatAnswer(text=answerText, citations=search.citations, reviewStatus=reviewStatus),
            audioUrl=job.audioUrl,
            animationUrl=job.animationUrl,
            jobId=job.id,
            agentTrace=trace,
        )
        self.turns[turn.id] = turn
        self._persistTurn(turn)
        return turn

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

    def _chunkText(self, text: str, targetWords: int) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: list[str] = []
        current: list[str] = []
        currentLength = 0
        for sentence in sentences:
            cleanSentence = " ".join(sentence.split())
            if not cleanSentence:
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
        return chunks or [" ".join(text.split())]

    def _citation(self, chunk: ChunkNode, score: float) -> Citation:
        document = self.documents[chunk.documentId]
        return Citation(
            chunkId=chunk.id,
            documentId=chunk.documentId,
            source=document.filename,
            page=chunk.page,
            titlePath=chunk.titlePath,
            excerpt=chunk.text[:360],
            confidence=max(0.0, min(1.0, score)),
        )

    def _answerFromCitations(self, query: str, citations: list[Citation]) -> str:
        lead = citations[0]
        support = " ".join(citation.excerpt for citation in citations[:2])
        condensed = support[:420].strip()
        return f"Based on {lead.source} page {lead.page}, {condensed} Source: {lead.source}, page {lead.page}."

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
        for chunk in chunks:
            expanded[chunk.id] = chunk
            for relatedId in chunk.relatedChunkIds:
                related = chunkById.get(relatedId)
                if related is not None:
                    expanded[related.id] = related
        return list(expanded.values())

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
        for path in sorted(self.settings.ragStorageDir.glob("documents/*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            document = DocumentDetail.model_validate(data)
            self.documents[document.id] = document
            embeddingPath = self.settings.ragStorageDir / "embeddings" / f"{document.id}.json"
            if embeddingPath.exists():
                embeddings = json.loads(embeddingPath.read_text(encoding="utf-8"))
                self.chunkEmbeddings.update({str(chunkId): [float(value) for value in vector] for chunkId, vector in embeddings.items()})

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
