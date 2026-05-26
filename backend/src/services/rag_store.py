from __future__ import annotations

import time
from threading import Lock
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid4, uuid5

import httpx

from src.config import Settings
from src.models.rag import AgentEvent, Document, DocumentDetail, PromptConfig, VoiceTurn


DEFAULT_PROMPTS = {
    "lead": "Bạn là leader agent. Phân rã câu hỏi, giao search task rõ ràng, chỉ yêu cầu context cần thiết.",
    "search": "Bạn là search agent. Phân tích query, chọn filter, tìm vector, mở rộng graph chunk, rerank, tự đánh giá và ghi nguồn.",
    "teacher": "Bạn là teacher agent. Trả lời có căn cứ từ context mới nhất, ưu tiên dữ liệu PDF hơn lịch sử.",
    "review": "Bạn là review agent. Kiểm hallucination, thiếu nguồn, trôi câu hỏi; nếu không ổn yêu cầu leader/search làm lại.",
    "upload": "Bạn là upload cleaner. Chuẩn hóa metadata PDF thành title, summary, keywords ngắn gọn.",
}

QDRANT_COLLECTION_LOCK = Lock()


class RagDatabaseStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._available = False
        self._initError = ""

    @property
    def available(self) -> bool:
        return self._available

    @property
    def initError(self) -> str:
        return self._initError

    def initialize(self) -> None:
        if not self.settings.postgresDsn:
            return
        try:
            import psycopg

            with psycopg.connect(self.settings.postgresDsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS rag_documents (
                            id TEXT PRIMARY KEY,
                            payload JSONB NOT NULL,
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        );
                        CREATE TABLE IF NOT EXISTS rag_chunks (
                            id TEXT PRIMARY KEY,
                            document_id TEXT NOT NULL,
                            payload JSONB NOT NULL,
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        );
                        CREATE TABLE IF NOT EXISTS rag_chunk_links (
                            source_chunk_id TEXT NOT NULL,
                            target_chunk_id TEXT NOT NULL,
                            link_type TEXT NOT NULL,
                            weight REAL NOT NULL DEFAULT 1,
                            PRIMARY KEY (source_chunk_id, target_chunk_id, link_type)
                        );
                        CREATE TABLE IF NOT EXISTS rag_prompts (
                            agent TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            content TEXT NOT NULL,
                            enabled BOOLEAN NOT NULL DEFAULT true,
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        );
                        CREATE TABLE IF NOT EXISTS rag_agent_sessions (
                            id TEXT PRIMARY KEY,
                            state TEXT NOT NULL,
                            question TEXT NOT NULL DEFAULT '',
                            answer TEXT NOT NULL DEFAULT '',
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        );
                        CREATE TABLE IF NOT EXISTS rag_agent_tasks (
                            id TEXT PRIMARY KEY,
                            session_id TEXT NOT NULL,
                            agent TEXT NOT NULL,
                            task TEXT NOT NULL,
                            status TEXT NOT NULL,
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        );
                        CREATE TABLE IF NOT EXISTS rag_agent_history (
                            id BIGSERIAL PRIMARY KEY,
                            session_id TEXT NOT NULL,
                            agent TEXT NOT NULL,
                            role TEXT NOT NULL,
                            message TEXT NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        );
                        CREATE TABLE IF NOT EXISTS rag_agent_context (
                            id BIGSERIAL PRIMARY KEY,
                            session_id TEXT NOT NULL,
                            agent TEXT NOT NULL,
                            context_type TEXT NOT NULL,
                            ref_id TEXT NOT NULL DEFAULT '',
                            content JSONB NOT NULL DEFAULT '{}'::jsonb,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        );
                        CREATE TABLE IF NOT EXISTS rag_agent_events (
                            id TEXT PRIMARY KEY,
                            session_id TEXT NOT NULL,
                            agent TEXT NOT NULL,
                            target TEXT,
                            event_type TEXT NOT NULL,
                            status TEXT NOT NULL,
                            message TEXT NOT NULL,
                            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        );
                        """
                    )
                    for agent, content in DEFAULT_PROMPTS.items():
                        cur.execute(
                            """
                            INSERT INTO rag_prompts(agent, name, content, enabled)
                            VALUES (%s, %s, %s, true)
                            ON CONFLICT (agent) DO NOTHING
                            """,
                            (agent, f"{agent.title()} prompt", content),
                        )
                conn.commit()
            self._available = True
            self._initError = ""
        except Exception as exc:
            self._available = False
            self._initError = str(exc)

    def loadDocuments(self) -> list[DocumentDetail]:
        if not self.available:
            return []
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(self.settings.postgresDsn, row_factory=dict_row) as conn:
            rows = conn.execute("SELECT payload FROM rag_documents ORDER BY updated_at").fetchall()
        return [DocumentDetail.model_validate(row["payload"]) for row in rows]

    def upsertDocument(self, document: DocumentDetail) -> None:
        if not self.available:
            return
        import psycopg
        from psycopg.types.json import Jsonb

        with psycopg.connect(self.settings.postgresDsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO rag_documents(id, payload, updated_at) VALUES (%s, %s, now()) ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload, updated_at = now()",
                    (document.id, Jsonb(document.model_dump(mode="json"))),
                )
                cur.execute("DELETE FROM rag_chunks WHERE document_id = %s", (document.id,))
                cur.execute("DELETE FROM rag_chunk_links WHERE source_chunk_id LIKE %s", (f"chk-{document.id}-%",))
                for chunk in document.chunks:
                    cur.execute(
                        "INSERT INTO rag_chunks(id, document_id, payload, updated_at) VALUES (%s, %s, %s, now()) ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload, updated_at = now()",
                        (chunk.id, document.id, Jsonb(chunk.model_dump(mode="json"))),
                    )
                    for relatedId in chunk.relatedChunkIds:
                        cur.execute(
                            "INSERT INTO rag_chunk_links(source_chunk_id, target_chunk_id, link_type, weight) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                            (chunk.id, relatedId, "wiki-related", 1.0),
                        )
            conn.commit()

    def deleteDocument(self, documentId: str) -> None:
        if not self.available:
            return
        import psycopg

        with psycopg.connect(self.settings.postgresDsn) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM rag_documents WHERE id = %s", (documentId,))
                cur.execute("DELETE FROM rag_chunks WHERE document_id = %s", (documentId,))
                cur.execute("DELETE FROM rag_chunk_links WHERE source_chunk_id LIKE %s OR target_chunk_id LIKE %s", (f"chk-{documentId}-%", f"chk-{documentId}-%"))
            conn.commit()

    def listPrompts(self) -> list[PromptConfig]:
        if not self.available:
            return [PromptConfig(agent=agent, name=f"{agent.title()} prompt", content=content, enabled=True) for agent, content in DEFAULT_PROMPTS.items()]
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(self.settings.postgresDsn, row_factory=dict_row) as conn:
            rows = conn.execute("SELECT agent, name, content, enabled, updated_at FROM rag_prompts ORDER BY agent").fetchall()
        return [
            PromptConfig(agent=row["agent"], name=row["name"], content=row["content"], enabled=row["enabled"], updatedAt=row["updated_at"].isoformat())
            for row in rows
        ]

    def promptFor(self, agent: str) -> str:
        prompts = {prompt.agent: prompt for prompt in self.listPrompts()}
        prompt = prompts.get(agent)
        return prompt.content if prompt and prompt.enabled else DEFAULT_PROMPTS.get(agent, "")

    def updatePrompt(self, agent: str, name: str | None, content: str | None, enabled: bool | None) -> PromptConfig:
        if not self.available:
            base = PromptConfig(agent=agent, name=name or f"{agent.title()} prompt", content=content or DEFAULT_PROMPTS.get(agent, ""), enabled=True if enabled is None else enabled)
            return base
        import psycopg
        from psycopg.rows import dict_row

        current = {prompt.agent: prompt for prompt in self.listPrompts()}.get(agent)
        nextPrompt = PromptConfig(
            agent=agent,
            name=name or (current.name if current else f"{agent.title()} prompt"),
            content=content or (current.content if current else DEFAULT_PROMPTS.get(agent, "")),
            enabled=(current.enabled if current else True) if enabled is None else enabled,
        )
        with psycopg.connect(self.settings.postgresDsn, row_factory=dict_row) as conn:
            row = conn.execute(
                """
                INSERT INTO rag_prompts(agent, name, content, enabled, updated_at)
                VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (agent) DO UPDATE SET name = EXCLUDED.name, content = EXCLUDED.content, enabled = EXCLUDED.enabled, updated_at = now()
                RETURNING agent, name, content, enabled, updated_at
                """,
                (agent, nextPrompt.name, nextPrompt.content, nextPrompt.enabled),
            ).fetchone()
            conn.commit()
        return PromptConfig(agent=row["agent"], name=row["name"], content=row["content"], enabled=row["enabled"], updatedAt=row["updated_at"].isoformat())

    def createSession(self, question: str, sessionId: str | None = None) -> str:
        sessionId = sessionId or str(uuid4())
        if self.available:
            import psycopg

            with psycopg.connect(self.settings.postgresDsn) as conn:
                conn.execute(
                    "INSERT INTO rag_agent_sessions(id, state, question) VALUES (%s, %s, %s) ON CONFLICT (id) DO UPDATE SET state = EXCLUDED.state, question = EXCLUDED.question, updated_at = now()",
                    (sessionId, "running", question),
                )
                conn.commit()
        return sessionId

    def updateSession(self, sessionId: str, state: str, answer: str = "") -> None:
        if not self.available:
            return
        import psycopg

        with psycopg.connect(self.settings.postgresDsn) as conn:
            conn.execute("UPDATE rag_agent_sessions SET state = %s, answer = %s, updated_at = now() WHERE id = %s", (state, answer, sessionId))
            conn.commit()

    def addEvent(self, event: AgentEvent) -> None:
        if not self.available:
            return
        import psycopg
        from psycopg.types.json import Jsonb

        with psycopg.connect(self.settings.postgresDsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO rag_agent_events(id, session_id, agent, target, event_type, status, message, metadata) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (event.id, event.sessionId, event.agent, event.target, event.eventType, event.status, event.message, Jsonb(event.metadata)),
                )
                cur.execute(
                    "INSERT INTO rag_agent_tasks(id, session_id, agent, task, status) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                    (f"task-{event.id}", event.sessionId, event.agent, event.message[:500], event.status),
                )
                cur.execute(
                    "INSERT INTO rag_agent_history(session_id, agent, role, message) VALUES (%s, %s, %s, %s)",
                    (event.sessionId, event.agent, "agent", event.message),
                )
                cur.execute(
                    "INSERT INTO rag_agent_context(session_id, agent, context_type, ref_id, content) VALUES (%s, %s, %s, %s, %s)",
                    (event.sessionId, event.agent, event.eventType, event.target or "", Jsonb(event.metadata)),
                )
            conn.commit()

    def listEvents(self, sessionId: str) -> list[AgentEvent]:
        if not self.available:
            return []
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(self.settings.postgresDsn, row_factory=dict_row) as conn:
            rows = conn.execute("SELECT * FROM rag_agent_events WHERE session_id = %s ORDER BY created_at, id", (sessionId,)).fetchall()
        return [
            AgentEvent(
                id=row["id"],
                sessionId=row["session_id"],
                agent=row["agent"],
                target=row["target"],
                eventType=row["event_type"],
                status=row["status"],
                message=row["message"],
                metadata=row["metadata"],
                createdAt=row["created_at"].isoformat(),
            )
            for row in rows
        ]


class QdrantVectorStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def isAvailable(self) -> bool:
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(f"{self.settings.qdrantUrl.rstrip('/')}/collections")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def ensureCollection(self, vectorSize: int) -> None:
        url = f"{self.settings.qdrantUrl.rstrip('/')}/collections/{self.settings.qdrantCollection}"
        with QDRANT_COLLECTION_LOCK:
            with httpx.Client(timeout=15) as client:
                existing = client.get(url)
                if existing.status_code == 200:
                    body = existing.json()
                    currentSize = body.get("result", {}).get("config", {}).get("params", {}).get("vectors", {}).get("size")
                    if currentSize == vectorSize:
                        return
                    client.delete(url).raise_for_status()
                    for _ in range(20):
                        if client.get(url).status_code == 404:
                            break
                        time.sleep(0.1)
                response = client.put(url, json={"vectors": {"size": vectorSize, "distance": "Cosine"}})
                if response.status_code == 409:
                    current = client.get(url)
                    currentSize = current.json().get("result", {}).get("config", {}).get("params", {}).get("vectors", {}).get("size") if current.status_code == 200 else None
                    if currentSize == vectorSize:
                        return
                response.raise_for_status()

    def upsertDocument(self, document: DocumentDetail, embeddings: dict[str, list[float]]) -> None:
        if not embeddings:
            return
        firstVector = next(iter(embeddings.values()))
        self.ensureCollection(len(firstVector))
        points = []
        for chunk in document.chunks:
            vector = embeddings.get(chunk.id)
            if not vector:
                continue
            points.append(
                {
                    "id": self._pointId(chunk.id),
                    "vector": vector,
                    "payload": {
                        "chunk_id": chunk.id,
                        "document_id": document.id,
                        "language": chunk.language.value,
                        "page": chunk.page,
                        "source": document.filename,
                        "text": chunk.text,
                    },
                }
            )
        if not points:
            return
        with httpx.Client(timeout=30) as client:
            response = client.put(f"{self.settings.qdrantUrl.rstrip('/')}/collections/{self.settings.qdrantCollection}/points?wait=true", json={"points": points})
            response.raise_for_status()

    def search(self, queryVector: list[float], language: str, limit: int) -> list[str]:
        if not self.isAvailable():
            return []
        payload = {"vector": queryVector, "limit": limit, "with_payload": True, "filter": {"must": [{"key": "language", "match": {"value": language}}]}}
        try:
            with httpx.Client(timeout=15) as client:
                response = client.post(f"{self.settings.qdrantUrl.rstrip('/')}/collections/{self.settings.qdrantCollection}/points/search", json=payload)
            if response.status_code != 200:
                return []
            body = response.json()
            return [str(item["payload"]["chunk_id"]) for item in body.get("result", []) if item.get("payload", {}).get("chunk_id")]
        except (httpx.HTTPError, ValueError, KeyError):
            return []

    def deleteDocument(self, documentId: str) -> None:
        if not self.isAvailable():
            return
        payload = {"filter": {"must": [{"key": "document_id", "match": {"value": documentId}}]}}
        with httpx.Client(timeout=15) as client:
            client.post(f"{self.settings.qdrantUrl.rstrip('/')}/collections/{self.settings.qdrantCollection}/points/delete?wait=true", json=payload)

    def _pointId(self, chunkId: str) -> str:
        return str(uuid5(NAMESPACE_URL, chunkId))
