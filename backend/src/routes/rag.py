from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query

from src.dependencies import getRagService, getRivaAsrClient
from src.models.rag import AgentSessionStatus, Document, DocumentDeleteResult, DocumentDetail, DocumentUpdateRequest, LanguageCode, PromptConfig, PromptUpdateRequest, RagRuntimeStatus, RagSearchRequest, RagSearchResult, Transcript, VoiceChatRequest, VoiceTurn
from src.services.riva_client import RivaAsrClient
from src.services.rag_service import RagService

router = APIRouter(prefix="/api", tags=["voice-rag"])


@router.get("/rag/status", response_model=RagRuntimeStatus)
def getRagStatus(ragService: RagService = Depends(getRagService)) -> RagRuntimeStatus:
    return ragService.status()


@router.post("/voice/transcribe", response_model=Transcript)
def transcribeVoice(
    payload: bytes = Body(..., media_type="application/octet-stream"),
    language: LanguageCode = Query(LanguageCode.english),
    contentType: str | None = Header(default=None, alias="content-type"),
    rivaAsrClient: RivaAsrClient = Depends(getRivaAsrClient),
) -> Transcript:
    try:
        return rivaAsrClient.transcribe(payload, contentType, language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/voice/chat", response_model=VoiceTurn)
def createVoiceTurn(request: VoiceChatRequest, ragService: RagService = Depends(getRagService)) -> VoiceTurn:
    try:
        return ragService.chat(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/chat/turns/{turnId}", response_model=VoiceTurn)
def getVoiceTurn(turnId: str, ragService: RagService = Depends(getRagService)) -> VoiceTurn:
    turn = ragService.getTurn(turnId)
    if turn is None:
        raise HTTPException(status_code=404, detail="turn not found")
    return turn


@router.get("/agent-sessions/{sessionId}", response_model=AgentSessionStatus)
def getAgentSession(sessionId: str, ragService: RagService = Depends(getRagService)) -> AgentSessionStatus:
    status = ragService.getSessionStatus(sessionId)
    if status.state == "unknown":
        raise HTTPException(status_code=404, detail="agent session not found")
    return status


@router.get("/prompts", response_model=list[PromptConfig])
def listPrompts(ragService: RagService = Depends(getRagService)) -> list[PromptConfig]:
    return ragService.listPrompts()


@router.patch("/prompts/{agent}", response_model=PromptConfig)
def updatePrompt(agent: str, request: PromptUpdateRequest, ragService: RagService = Depends(getRagService)) -> PromptConfig:
    return ragService.updatePrompt(agent, request)


@router.post("/documents", response_model=DocumentDetail)
def ingestDocument(
    payload: bytes = Body(..., media_type="application/pdf"),
    filename: str = Query(..., min_length=1, max_length=180),
    language: LanguageCode = Query(LanguageCode.english),
    contentType: str | None = Header(default=None, alias="content-type"),
    ragService: RagService = Depends(getRagService),
) -> DocumentDetail:
    if contentType and "application/pdf" not in contentType.lower():
        raise HTTPException(status_code=415, detail="content-type must be application/pdf")
    try:
        return ragService.ingestBytes(payload, filename, language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/documents", response_model=list[Document])
def listDocuments(ragService: RagService = Depends(getRagService)) -> list[Document]:
    return ragService.listDocuments()


@router.get("/documents/{documentId}", response_model=DocumentDetail)
def getDocument(documentId: str, ragService: RagService = Depends(getRagService)) -> DocumentDetail:
    document = ragService.getDocument(documentId)
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    return document


@router.patch("/documents/{documentId}", response_model=DocumentDetail)
def updateDocument(documentId: str, request: DocumentUpdateRequest, ragService: RagService = Depends(getRagService)) -> DocumentDetail:
    document = ragService.updateDocument(documentId, request)
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    return document


@router.delete("/documents/{documentId}", response_model=DocumentDeleteResult)
def deleteDocument(documentId: str, ragService: RagService = Depends(getRagService)) -> DocumentDeleteResult:
    result = ragService.deleteDocument(documentId)
    if result is None:
        raise HTTPException(status_code=404, detail="document not found")
    return result


@router.get("/documents/{documentId}/chunks")
def getDocumentChunks(documentId: str, ragService: RagService = Depends(getRagService)) -> list:
    chunks = ragService.getChunks(documentId)
    if chunks is None:
        raise HTTPException(status_code=404, detail="document not found")
    return chunks


@router.post("/rag/search", response_model=RagSearchResult)
def searchKnowledge(request: RagSearchRequest, ragService: RagService = Depends(getRagService)) -> RagSearchResult:
    try:
        return ragService.search(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
