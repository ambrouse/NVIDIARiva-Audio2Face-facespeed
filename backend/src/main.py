import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.config import getSettings
from src.dependencies import getServiceManager
from src.models.service import ServiceName
from src.routes import artifacts, jobs, rag, services, system

settings = getSettings()
app = FastAPI(title="FaceSpeed Voice RAG API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowedOriginList,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(services.router)
app.include_router(jobs.router)
app.include_router(artifacts.router)
app.include_router(system.router)
app.include_router(rag.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/logs/{serviceName}")
async def streamLogs(websocket: WebSocket, serviceName: ServiceName) -> None:
    await websocket.accept()
    serviceManager = getServiceManager()
    lastSize = 0
    try:
        while True:
            lines = serviceManager.readLogs(serviceName, 100)
            for line in lines[lastSize:]:
                await websocket.send_text(line)
            lastSize = len(lines)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
