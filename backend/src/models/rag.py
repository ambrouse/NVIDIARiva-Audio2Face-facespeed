from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class LanguageCode(StrEnum):
    english = "en-US"
    vietnamese = "vi-VN"


class IngestionStatus(StrEnum):
    indexed = "indexed"
    failed = "failed"


class AgentName(StrEnum):
    lead = "lead"
    search = "search"
    review = "review"
    teacher = "teacher"


class ReviewStatus(StrEnum):
    passed = "pass"
    notFound = "not_found"
    retrySearch = "retry_search"
    unsafeOrUnanswerable = "unsafe_or_unanswerable"


class Transcript(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    language: LanguageCode = LanguageCode.english
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = Field(default="asr", min_length=1, max_length=32)

    @field_validator("text")
    @classmethod
    def normalizeText(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("transcript cannot be empty")
        return normalized


class Citation(BaseModel):
    chunkId: str
    documentId: str
    source: str
    page: int = Field(ge=1)
    titlePath: list[str] = Field(default_factory=list)
    excerpt: str = Field(min_length=1, max_length=700)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str = Field(min_length=1, max_length=180)
    title: str = Field(min_length=1, max_length=180)
    language: LanguageCode = LanguageCode.english
    status: IngestionStatus = IngestionStatus.indexed
    checksum: str = Field(min_length=16, max_length=128)
    pageCount: int = Field(default=1, ge=1)
    chunkCount: int = Field(default=0, ge=0)
    summary: str = Field(default="", max_length=500)
    parseProvider: str = Field(default="docling", max_length=32)
    embeddingProvider: str = Field(default="embedding-api", max_length=32)
    rerankProvider: str = Field(default="embedding-api", max_length=32)


class SectionNode(BaseModel):
    id: str
    documentId: str
    title: str
    titlePath: list[str]
    level: int = Field(ge=1, le=6)
    pageStart: int = Field(ge=1)
    pageEnd: int = Field(ge=1)
    parentId: str | None = None
    childIds: list[str] = Field(default_factory=list)


class ChunkNode(BaseModel):
    id: str
    documentId: str
    sectionId: str
    text: str = Field(min_length=1, max_length=2400)
    page: int = Field(ge=1)
    titlePath: list[str] = Field(default_factory=list)
    language: LanguageCode = LanguageCode.english
    tokenCount: int = Field(ge=1)
    previousChunkId: str | None = None
    nextChunkId: str | None = None
    relatedChunkIds: list[str] = Field(default_factory=list)
    embeddingId: str | None = None


class DocumentDetail(Document):
    sections: list[SectionNode] = Field(default_factory=list)
    chunks: list[ChunkNode] = Field(default_factory=list)


class AgentTrace(BaseModel):
    agent: AgentName
    status: str
    message: str = Field(max_length=600)
    evidenceChunkIds: list[str] = Field(default_factory=list)


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    language: LanguageCode = LanguageCode.english
    topK: int = Field(default=5, ge=1, le=12)

    @field_validator("query")
    @classmethod
    def normalizeQuery(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("query cannot be empty")
        return normalized


class RagSearchResult(BaseModel):
    query: str
    found: bool
    confidence: float = Field(ge=0.0, le=1.0)
    answerability: ReviewStatus
    citations: list[Citation] = Field(default_factory=list)
    compactContext: str = ""
    trace: list[AgentTrace] = Field(default_factory=list)


class VoiceChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    language: LanguageCode = LanguageCode.english
    voice: str = Field(default="English-US.Female-1", min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    outputMode: str = Field(default="preview", pattern=r"^(preview|export|stream)$")

    @field_validator("message")
    @classmethod
    def normalizeMessage(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("message cannot be empty")
        return normalized


class ChatAnswer(BaseModel):
    text: str
    citations: list[Citation] = Field(default_factory=list)
    reviewStatus: ReviewStatus


class VoiceTurn(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    language: LanguageCode
    transcript: Transcript
    answer: ChatAnswer
    audioUrl: str | None = None
    animationUrl: str | None = None
    jobId: str | None = None
    agentTrace: list[AgentTrace] = Field(default_factory=list)


class RagRuntimeStatus(BaseModel):
    asrAvailable: bool
    asrDetail: str
    documentCount: int
    chunkCount: int
    languages: list[LanguageCode]
    doclingBaseUrl: str
    embeddingBaseUrl: str
    parseProvider: str = "docling"
    retrievalProvider: str = "embedding-rerank"
