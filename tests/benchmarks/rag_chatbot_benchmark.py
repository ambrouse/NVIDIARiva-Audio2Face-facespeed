#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import statistics
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from resource_guard import ResourceGuard, ResourceGuardError, ResourceThresholds, start_resource_monitor  # noqa: E402

RUNS_DIR = ROOT / "tests" / "benchmarks" / "runs"
QUESTION_TEMPLATES = [
    "What does the indexed PDF say in the passage containing: \"{topic}\"?",
    "Answer from the indexed PDF only. What is discussed around: \"{topic}\"?",
    "Summarize the source evidence around this phrase: \"{topic}\".",
    "Which PDF details support the phrase: \"{topic}\"?",
    "Use citations to explain the passage containing: \"{topic}\".",
]
STOPWORDS = {
    "about", "above", "according", "address", "answer", "application", "chunk", "could", "document",
    "from", "have", "image", "indexed", "mention", "nguyen", "page", "source", "that", "this",
    "trong", "with", "what", "which", "your",
}
REQUIRED_EDGES = {
    ("user", "lead"),
    ("lead", "search"),
    ("search", "qdrant"),
    ("teacher", "llm"),
    ("review", "lead"),
}
CONTENT_TERMS = {
    "algorithm", "analysis", "approach", "architecture", "benchmark", "context", "data", "dataset",
    "evaluation", "experiment", "framework", "learning", "method", "model", "network", "performance",
    "pipeline", "propose", "retrieval", "results", "robustness", "system", "task", "training",
}
NOISE_TOPIC_TERMS = {
    "arxiv", "bibliography", "conference", "doi", "formula-not-decoded", "http", "https",
    "model's input", "preprint", "proceedings", "question verbatim", "references",
    "source article", "standard prompt", "url", "verbatim from", "www",
}


@dataclass(frozen=True)
class Case:
    id: str
    question: str
    document_id: str
    document_name: str
    chunk_id: str
    page: int
    topic: str
    keywords: list[str]
    source_excerpt: str


def main() -> None:
    parser = argparse.ArgumentParser(description="Run real API benchmark for the RAG chatbot.")
    parser.add_argument("--api-base", default="http://127.0.0.1:6320")
    parser.add_argument("--count", type=int, required=True, choices=[1, 5, 10, 30, 100, 300, 500])
    parser.add_argument("--concurrency", type=int, default=1, choices=[1, 10], help="Simulated concurrent users for the same real API flow.")
    parser.add_argument("--file-count", type=int, default=0, choices=[0, 10, 100, 1000], help="0 means use every indexed document; otherwise require and benchmark exactly this many indexed files.")
    parser.add_argument("--threshold", type=float, default=0.95)
    parser.add_argument("--record-best", action="store_true", help="Persist only if this run passes the threshold.")
    parser.add_argument("--keep-failures", action="store_true", help="Persist failed runs for debugging.")
    parser.add_argument("--artifact-samples", type=int, default=3, help="Download audio/animation for first N cases.")
    parser.add_argument("--voice", default="English-US.Female-1")
    parser.add_argument("--language", default="en-US")
    parser.add_argument("--llm-base", default="http://127.0.0.1:6107/v1")
    parser.add_argument("--llm-model", default="google/gemma-4-E4B-it")
    parser.add_argument("--ram-min-free-percent", type=float, default=10.0)
    parser.add_argument("--gpu-min-free-vram-percent", type=float, default=10.0)
    parser.add_argument("--disk-min-free-percent", type=float, default=10.0)
    parser.add_argument("--resource-check-interval", type=float, default=5.0)
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    guard = ResourceGuard(
        ROOT,
        ResourceThresholds(
            ram_min_free_percent=args.ram_min_free_percent,
            gpu_min_free_vram_percent=args.gpu_min_free_vram_percent,
            disk_min_free_percent=args.disk_min_free_percent,
        ),
    )
    guard.assert_safe("benchmark-start")
    status = api_get(args.api_base, "/api/rag/status")
    documents = api_get(args.api_base, "/api/documents")
    documents = select_documents(documents, args.file_count)
    if not documents:
        raise SystemExit("No indexed PDF documents are available for benchmark.")

    chunks_by_doc: dict[str, list[dict[str, Any]]] = {}
    for document in documents:
        chunks_by_doc[document["id"]] = api_get(args.api_base, f"/api/documents/{document['id']}/chunks")
    cases = build_cases(documents, chunks_by_doc, args.count)

    results: list[dict[str, Any]] = []
    artifact_dir = RUNS_DIR / "_latest-artifacts"
    if artifact_dir.exists():
        shutil.rmtree(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    run_dir = run_directory(args.count, args.file_count, args.concurrency)
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    abort_event = threading.Event()
    stop_event = threading.Event()
    monitor = start_resource_monitor(guard, abort_event, stop_event, args.resource_check_interval)
    try:
        if args.concurrency == 1:
            for index, case in enumerate(cases, start=1):
                if abort_event.is_set():
                    raise ResourceGuardError("Resource guard stopped the benchmark from the background monitor.")
                result = run_case(index, case, args, artifact_dir, guard, abort_event)
                results.append(result)
                checkpoint = summarize(status, documents, cases[:len(results)], results, started, datetime.now(timezone.utc), args.threshold, args.concurrency, guard.samples)
                apply_completion_gate(checkpoint, args.count, args.file_count)
                write_report(run_dir, checkpoint, results)
                print_case_result(index, args.count, result, case)
        else:
            pending: dict[Any, tuple[int, Case]] = {}
            next_index = 1
            with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                while next_index <= len(cases) or pending:
                    if abort_event.is_set():
                        raise ResourceGuardError("Resource guard stopped the benchmark from the background monitor.")
                    while next_index <= len(cases) and len(pending) < args.concurrency:
                        guard.assert_safe(f"before-schedule-{next_index:04d}")
                        case = cases[next_index - 1]
                        future = executor.submit(run_case, next_index, case, args, artifact_dir, guard, abort_event)
                        pending[future] = (next_index, case)
                        next_index += 1
                    for future in as_completed(list(pending)):
                        index, case = pending.pop(future)
                        result = future.result()
                        results.append(result)
                        checkpoint = summarize(status, documents, cases[:len(results)], results, started, datetime.now(timezone.utc), args.threshold, args.concurrency, guard.samples)
                        apply_completion_gate(checkpoint, args.count, args.file_count)
                        write_report(run_dir, checkpoint, results)
                        print_case_result(index, args.count, result, case)
                        break
    finally:
        stop_event.set()
        monitor.join(timeout=2)

    results = sorted(results, key=lambda result: int(result.get("caseIndex", 0)))
    summary = summarize(status, documents, cases, results, started, datetime.now(timezone.utc), args.threshold, args.concurrency, guard.samples)
    apply_completion_gate(summary, args.count, args.file_count)
    write_report(run_dir, summary, results)
    if artifact_dir.exists():
        shutil.move(str(artifact_dir), run_dir / "artifacts")

    if summary["accepted"]:
        best_dir = best_directory(args.count, args.file_count, args.concurrency)
        if args.record_best:
            if best_dir.exists():
                shutil.rmtree(best_dir)
            shutil.copytree(run_dir, best_dir)
        print(f"PASS {args.count} concurrency={args.concurrency}: score={summary['overallPassRate']:.3%}, report={run_dir}")
    else:
        if not args.keep_failures:
            shutil.rmtree(run_dir)
        print(f"FAIL {args.count} concurrency={args.concurrency}: score={summary['overallPassRate']:.3%}, threshold={args.threshold:.1%}")
        raise SystemExit(2)


def run_case(index: int, case: Case, args: argparse.Namespace, artifact_dir: Path, guard: ResourceGuard, abort_event: threading.Event) -> dict[str, Any]:
    guard.assert_safe(f"before-case-{index:04d}")
    if abort_event.is_set():
        raise ResourceGuardError("Resource guard stopped before starting a new case.")
    session_id = f"bench-{args.count}-c{args.concurrency}-{index:04d}-{uuid4().hex[:8]}"
    payload = {
        "message": case.question,
        "language": args.language,
        "voice": args.voice,
        "outputMode": "preview",
        "sessionId": session_id,
    }
    t0 = time.perf_counter()
    error = ""
    turn: dict[str, Any] | None = None
    attempts = 0
    try:
        turn, attempts = post_with_retry(args.api_base, "/api/voice/chat", payload, timeout=180, retries=2)
    except Exception as exc:  # noqa: BLE001 - benchmark records external API failure.
        error = str(exc)
    latency = time.perf_counter() - t0
    session = {}
    if turn and turn.get("sessionId"):
        try:
            session = api_get(args.api_base, f"/api/agent-sessions/{turn['sessionId']}")
        except Exception as exc:  # noqa: BLE001
            session = {"error": str(exc), "events": []}

    result = evaluate_case(case, turn, session, latency, error)
    if turn:
        result["judge"] = judge_answer(args.llm_base, args.llm_model, case, turn)
        result["checks"]["judge_correct"] = result["judge"].get("correct") is True
        result["checks"]["judge_grounded"] = result["judge"].get("grounded") is True
        result["checks"]["judge_no_hallucination"] = result["judge"].get("hallucination") is False
        result["score"] = sum(1 for value in result["checks"].values() if value) / len(result["checks"])
        result["status"] = "pass" if all(result["checks"].values()) else "fail"
    result["attempts"] = attempts
    result["caseIndex"] = index
    result["concurrency"] = args.concurrency
    if turn and index <= args.artifact_samples:
        result["artifactEvidence"] = download_artifacts(args.api_base, turn, artifact_dir, index)
    guard.assert_safe(f"after-case-{index:04d}")
    return result


def print_case_result(index: int, total: int, result: dict[str, Any], case: Case) -> None:
    print(f"{index:04d}/{total} {result['status']} score={result['score']:.3f} attempts={result.get('attempts', 0)} latency={result['latencySeconds']:.2f}s {case.topic}", flush=True)


def api_get(base_url: str, path: str, timeout: int = 30) -> Any:
    request = urllib.request.Request(f"{base_url.rstrip('/')}{path}", headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def api_post(base_url: str, path: str, payload: dict[str, Any], timeout: int = 120) -> Any:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def post_with_retry(base_url: str, path: str, payload: dict[str, Any], timeout: int, retries: int) -> tuple[Any, int]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 2):
        try:
            return api_post(base_url, path, payload, timeout=timeout), attempt
        except RuntimeError as exc:
            last_error = exc
            if "HTTP 500" not in str(exc) and "HTTP 503" not in str(exc):
                raise
            if attempt > retries:
                break
            time.sleep(1.5 * attempt)
    raise last_error or RuntimeError("request failed")


def select_documents(documents: list[dict[str, Any]], file_count: int) -> list[dict[str, Any]]:
    indexed = [document for document in documents if str(document.get("status", "indexed")) == "indexed"]
    indexed = sorted(indexed, key=lambda document: (str(document.get("filename") or ""), str(document.get("id") or "")))
    if file_count == 0:
        return indexed
    if len(indexed) < file_count:
        raise SystemExit(f"Need {file_count} indexed PDF files, but only {len(indexed)} are available. Do not mark this benchmark as passed.")
    return indexed[:file_count]


def run_directory(count: int, file_count: int, concurrency: int) -> Path:
    suffix = f"_latest-{count}" if concurrency == 1 else f"_latest-{count}-users-{concurrency}"
    if file_count:
        return RUNS_DIR / "matrix" / f"file-{file_count}" / suffix
    return RUNS_DIR / suffix


def best_directory(count: int, file_count: int, concurrency: int) -> Path:
    suffix = f"best-{count}" if concurrency == 1 else f"best-{count}-users-{concurrency}"
    if file_count:
        return RUNS_DIR / "matrix" / f"file-{file_count}" / suffix
    return RUNS_DIR / suffix


def apply_completion_gate(summary: dict[str, Any], target_count: int, file_count: int) -> None:
    summary["targetCaseCount"] = target_count
    summary["targetFileCount"] = file_count or summary["documentCount"]
    summary["complete"] = summary["caseCount"] == target_count
    summary["accepted"] = bool(summary["accepted"] and summary["complete"])


def build_cases(documents: list[dict[str, Any]], chunks_by_doc: dict[str, list[dict[str, Any]]], count: int) -> list[Case]:
    seedsByDocument: list[list[Case]] = []
    for document in documents:
        documentSeeds: list[Case] = []
        for chunk in chunks_by_doc.get(document["id"], []):
            text = " ".join(str(chunk.get("text", "")).split())
            if is_reference_chunk(chunk, text):
                continue
            if ascii_ratio(text) < 0.72 or len(text.split()) < 30:
                continue
            keywords = keywords_from_text(text)
            if len(keywords) < 5:
                continue
            if len(set(keywords) & CONTENT_TERMS) < 2:
                continue
            for offset, topic in enumerate(topic_windows(text)):
                if not is_benchmark_topic(topic):
                    continue
                if len(set(keywords_from_text(topic)) & CONTENT_TERMS) < 1:
                    continue
                template = QUESTION_TEMPLATES[(len(documentSeeds) + offset) % len(QUESTION_TEMPLATES)]
                page = int(chunk.get("page") or 1)
                topicKeywords = keywords_from_text(topic)
                documentSeeds.append(
                    Case(
                        id=f"{document['id']}-{chunk['id']}-{offset}",
                        question=template.format(page=page, topic=topic),
                        document_id=document["id"],
                        document_name=str(document.get("filename") or document.get("title") or document["id"]),
                        chunk_id=chunk["id"],
                        page=page,
                        topic=topic,
                        keywords=topicKeywords[:10] or keywords[:10],
                        source_excerpt=text[:1200],
                    )
                )
        if documentSeeds:
            seedsByDocument.append(documentSeeds)
    seeds = round_robin(seedsByDocument)
    if not seeds:
        raise SystemExit("No usable chunk text is available to build benchmark questions.")
    return [seeds[index % len(seeds)] for index in range(count)]


def round_robin(groups: list[list[Case]]) -> list[Case]:
    output: list[Case] = []
    depth = max((len(group) for group in groups), default=0)
    for index in range(depth):
        for group in groups:
            if index < len(group):
                output.append(group[index])
    return output


def keywords_from_text(text: str) -> list[str]:
    raw = []
    current = []
    for char in text:
        current.append(char.lower() if char.isalnum() else " ")
    for token in "".join(current).split():
        if len(token) >= 4 and token not in STOPWORDS and not token.isdigit():
            raw.append(token)
    deduped: list[str] = []
    for token in raw:
        if token not in deduped:
            deduped.append(token)
    return deduped


def topic_windows(text: str) -> list[str]:
    words = []
    for rawWord in text.split():
        clean = rawWord.strip(".,;:()[]{}<>\"'").lower()
        if not clean or len(clean) > 24 or clean.isdigit():
            continue
        words.append(clean)
    windows = []
    for start in range(0, min(len(words), 100), 12):
        window = words[start:start + 10]
        content = [word for word in window if len(word) >= 4 and word not in STOPWORDS]
        if len(content) >= 4:
            windows.append(" ".join(window))
        if len(windows) >= 3:
            break
    return windows or [" ".join(words[:8])]


def is_benchmark_topic(topic: str) -> bool:
    lowered = topic.lower()
    if not topic.isascii():
        return False
    if "%" in topic:
        return False
    if any(term in lowered for term in NOISE_TOPIC_TERMS):
        return False
    if any(symbol in topic for symbol in ["=", "{", "}", "\\", "^", "ˆ", "∈", "≤", "≥", "→", "←"]):
        return False
    tokens = topic.split()
    digitTokens = [token for token in tokens if any(char.isdigit() for char in token)]
    if tokens and any(char.isdigit() for char in tokens[0]):
        return False
    if len(digitTokens) > 2:
        return False
    if any(len(token) == 1 and not token.isdigit() for token in tokens):
        return False
    return len([token for token in tokens if len(token) >= 4 and token not in STOPWORDS]) >= 4


def is_reference_chunk(chunk: dict[str, Any], text: str) -> bool:
    titlePath = " ".join(str(value) for value in chunk.get("titlePath", [])).lower()
    lowered = text.lower()
    if any(term in titlePath for term in ["references", "bibliography"]):
        return True
    if any(term in lowered for term in ["question ( verbatim", "standard prompt preamble", "source article reports verbatim"]):
        return True
    if sum(lowered.count(option) for option in ["- (a)", "- (b)", "- (c)", "- (d)", "- (e)"]) >= 3:
        return True
    citationSignals = sum(
        [
            lowered.count("http://") + lowered.count("https://") + lowered.count(" url "),
            lowered.count(" in proceedings "),
            lowered.count(" international conference "),
            lowered.count(" arxiv"),
            lowered.count(" preprint"),
        ]
    )
    if citationSignals >= 2:
        return True
    if "advances in neural information processing systems" in lowered and "conference" in lowered:
        return True
    return False


def ascii_ratio(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    ascii_letters = [char for char in letters if char.isascii()]
    return len(ascii_letters) / len(letters)


def evaluate_case(case: Case, turn: dict[str, Any] | None, session: dict[str, Any], latency: float, error: str) -> dict[str, Any]:
    if not turn:
        return {
            "caseId": case.id,
            "question": case.question,
            "status": "fail",
            "score": 0.0,
            "latencySeconds": latency,
            "error": error,
            "checks": {"api": False},
        }
    answer = turn.get("answer", {})
    text = str(answer.get("text", ""))
    citations = answer.get("citations", []) or []
    events = session.get("events", []) or turn.get("agentEvents", []) or []
    citation_pages = {int(citation.get("page") or 0) for citation in citations}
    citation_chunks = {str(citation.get("chunkId", "")) for citation in citations}
    citation_documents = {str(citation.get("documentId", "")) for citation in citations}
    citation_sources = {str(citation.get("source", "")) for citation in citations}
    event_edges = {(str(event.get("agent")), str(event.get("target"))) for event in events}
    answer_norm = text.lower()
    answer_source, answer_page = answer_source_reference(text)
    keyword_hits = [keyword for keyword in case.keywords if keyword.lower() in answer_norm]
    not_found_phrases = [
        "could not find",
        "cannot find",
        "does not contain",
        "not contain",
        "not present",
        "no relevant",
        "no source",
        "không tìm thấy",
        "không có trong",
    ]
    expected_document_cited = case.document_id in citation_documents or case.document_name in citation_sources
    expected_chunk_cited = case.chunk_id in citation_chunks
    expected_page_cited = case.page in citation_pages
    answer_source_cited = bool(answer_source and answer_page and any(
        str(citation.get("source", "")) == answer_source and int(citation.get("page") or 0) == answer_page
        for citation in citations
    ))
    answer_source_expected_document = bool(answer_source and answer_source == case.document_name)
    checks = {
        "api": True,
        "review_pass": answer.get("reviewStatus") == "pass",
        "has_answer": len(text.split()) >= 12,
        "has_citations": len(citations) > 0,
        "answer_source_cited": answer_source_cited,
        "answer_source_expected_document": answer_source_expected_document,
        "keyword_overlap": len(keyword_hits) >= 1,
        "expected_document_cited": expected_document_cited,
        "expected_chunk_cited": expected_chunk_cited,
        "expected_page_cited": expected_page_cited,
        "answer_not_unjustified_not_found": not any(phrase in answer_norm for phrase in not_found_phrases),
        "dashboard_edges": REQUIRED_EDGES.issubset(event_edges),
        "audio_url": bool(turn.get("audioUrl")),
        "animation_url": bool(turn.get("animationUrl")),
        "latency_ok": latency <= 180,
    }
    score = sum(1 for value in checks.values() if value) / len(checks)
    return {
        "caseId": case.id,
        "question": case.question,
        "expected": {
            "documentId": case.document_id,
            "documentName": case.document_name,
            "chunkId": case.chunk_id,
            "page": case.page,
            "topic": case.topic,
            "keywords": case.keywords,
            "sourceExcerpt": case.source_excerpt,
        },
        "answerText": text,
        "answerPreview": text[:600],
        "reviewStatus": answer.get("reviewStatus"),
        "citationCount": len(citations),
        "citationPages": sorted(citation_pages),
        "citations": citations,
        "diagnostics": {
            "expected_page": expected_page_cited,
            "expected_chunk": expected_chunk_cited,
            "answer_source": answer_source,
            "answer_page": answer_page,
        },
        "keywordHits": keyword_hits,
        "eventEdges": sorted(f"{left}->{right}" for left, right in event_edges),
        "latencySeconds": latency,
        "checks": checks,
        "score": score,
        "status": "pass" if all(checks.values()) else "fail",
    }


def answer_source_reference(text: str) -> tuple[str, int | None]:
    match = re.search(r"\bSource:\s*([^,\n]+),\s*page\s+(\d+)", text, flags=re.IGNORECASE)
    if not match:
        return "", None
    return match.group(1).strip(), int(match.group(2))


def download_artifacts(base_url: str, turn: dict[str, Any], artifact_dir: Path, index: int) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for key, suffix in [("audioUrl", "answer.wav"), ("animationUrl", "animation.json")]:
        url = turn.get(key)
        if not url:
            evidence[key] = {"ok": False, "reason": "missing url"}
            continue
        destination = artifact_dir / f"{index:03d}-{suffix}"
        try:
            with urllib.request.urlopen(f"{base_url.rstrip('/')}{url}", timeout=30) as response:
                body = response.read()
            destination.write_bytes(body)
            evidence[key] = {"ok": True, "path": str(destination.relative_to(ROOT)), "bytes": len(body)}
        except Exception as exc:  # noqa: BLE001
            evidence[key] = {"ok": False, "reason": str(exc)}
    return evidence


def judge_answer(llm_base: str, model: str, case: Case, turn: dict[str, Any]) -> dict[str, Any]:
    answer = turn.get("answer", {})
    citations = answer.get("citations", []) or []
    source_context = "\n".join(
        f"[{citation.get('source')} p.{citation.get('page')}] {citation.get('excerpt', '')}"
        for citation in citations[:5]
    )
    user_content = (
        "Evaluate whether the answer is correct and grounded in the cited source context.\n"
        "This benchmark question is known to be answerable from the ground-truth PDF source below.\n"
        "Mark correct=false if the answer says the information is not found, if it cites the wrong file, "
        "or if it gives a generic/partial answer instead of answering the requested source passage.\n"
        "Return only JSON with keys: correct (bool), grounded (bool), hallucination (bool), score (0-1), reason (short string).\n"
        f"Question: {case.question}\n"
        f"Ground-truth source: {case.document_name}, page {case.page}, chunk {case.chunk_id}\n"
        f"Ground-truth excerpt: {case.source_excerpt[:1000]}\n"
        f"Expected topic keywords: {', '.join(case.keywords)}\n"
        f"Answer: {answer.get('text', '')}\n"
        f"Cited context:\n{source_context}\n"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a strict RAG benchmark judge. Do not reward unsupported claims."},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0,
        "max_tokens": 220,
    }
    request = urllib.request.Request(
        f"{llm_base.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.strip("`")
            content = content.removeprefix("json").strip()
        start = content.find("{")
        end = content.rfind("}")
        parsed = json.loads(content[start:end + 1] if start >= 0 and end >= start else content)
        return {
            "correct": bool(parsed.get("correct")),
            "grounded": bool(parsed.get("grounded")),
            "hallucination": bool(parsed.get("hallucination")),
            "score": float(parsed.get("score", 0.0)),
            "reason": str(parsed.get("reason", ""))[:500],
        }
    except Exception as exc:  # noqa: BLE001
        return {"correct": False, "grounded": False, "hallucination": True, "score": 0.0, "reason": f"judge failed: {exc}"}


def summarize(
    status: dict[str, Any],
    documents: list[dict[str, Any]],
    cases: list[Case],
    results: list[dict[str, Any]],
    started: datetime,
    finished: datetime,
    threshold: float,
    concurrency: int,
    resource_samples: list[dict[str, Any]],
) -> dict[str, Any]:
    pass_count = sum(1 for result in results if result["status"] == "pass")
    latencies = [float(result["latencySeconds"]) for result in results]
    check_names = sorted({name for result in results for name in result.get("checks", {})})
    check_rates = {
        name: sum(1 for result in results if result.get("checks", {}).get(name)) / len(results)
        for name in check_names
    }
    overall = pass_count / len(results)
    return {
        "startedAt": started.isoformat(),
        "finishedAt": finished.isoformat(),
        "durationSeconds": (finished - started).total_seconds(),
        "caseCount": len(cases),
        "documentCount": len(documents),
        "chunkCount": status.get("chunkCount"),
        "runtime": status,
        "concurrency": concurrency,
        "passCount": pass_count,
        "failCount": len(results) - pass_count,
        "overallPassRate": overall,
        "accepted": overall > threshold and all(rate > threshold for rate in check_rates.values()),
        "threshold": threshold,
        "checkPassRates": check_rates,
        "latency": {
            "p50": percentile(latencies, 50),
            "p95": percentile(latencies, 95),
            "max": max(latencies) if latencies else 0,
            "mean": statistics.mean(latencies) if latencies else 0,
        },
        "resourceSamples": resource_samples[-20:],
    }


def percentile(values: list[float], pct: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = math.ceil((pct / 100) * len(ordered)) - 1
    return ordered[max(0, min(index, len(ordered) - 1))]


def write_report(run_dir: Path, summary: dict[str, Any], results: list[dict[str, Any]]) -> None:
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_case_log(run_dir, results)
    lines = [
        f"# RAG Chatbot Benchmark {summary['caseCount']}",
        "",
        f"- Accepted: `{summary['accepted']}`",
        f"- Complete: `{summary.get('complete')}`",
        f"- Pass rate: `{summary['overallPassRate']:.2%}`",
        f"- Pass/fail: `{summary['passCount']}/{summary['failCount']}`",
        f"- Concurrency: `{summary.get('concurrency')}`",
        f"- Target file/case count: `{summary.get('targetFileCount')}/{summary.get('targetCaseCount')}`",
        f"- Documents/chunks: `{summary['documentCount']}/{summary['chunkCount']}`",
        f"- Duration: `{summary['durationSeconds']:.1f}s`",
        f"- Latency p50/p95/max: `{summary['latency']['p50']:.2f}s / {summary['latency']['p95']:.2f}s / {summary['latency']['max']:.2f}s`",
        "",
        "## Check Pass Rates",
        "",
    ]
    for name, rate in summary["checkPassRates"].items():
        lines.append(f"- `{name}`: `{rate:.2%}`")
    resource_samples = summary.get("resourceSamples") or []
    if resource_samples:
        latest = resource_samples[-1]
        ram = latest.get("ram") or {}
        gpu = latest.get("gpu") or {}
        disk = latest.get("disk") or {}
        lines.extend(
            [
                "",
                "## Resource Guard",
                "",
                f"- Latest RAM free: `{ram.get('freePercent', 0):.2f}%`",
                f"- Latest VRAM free: `{gpu.get('freeVramPercent', 0):.2f}%`",
                f"- Latest disk free: `{disk.get('freePercent', 0):.2f}%`",
            ]
        )
    failures = [result for result in results if result["status"] != "pass"][:10]
    if failures:
        lines.extend(["", "## First Failures", ""])
        for result in failures:
            failed_checks = [name for name, ok in result.get("checks", {}).items() if not ok]
            lines.append(f"- `{result['caseId']}`: {', '.join(failed_checks)}")
    (run_dir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_case_log(run_dir: Path, results: list[dict[str, Any]]) -> None:
    jsonlLines = []
    markdown = ["# Case Output Log", ""]
    for index, result in enumerate(results, start=1):
        judge = result.get("judge") or {}
        checks = result.get("checks") or {}
        failedChecks = [name for name, ok in checks.items() if not ok]
        citations = [
            {
                "source": citation.get("source"),
                "page": citation.get("page"),
                "chunkId": citation.get("chunkId"),
                "confidence": citation.get("confidence"),
            }
            for citation in result.get("citations", [])
        ]
        logItem = {
            "index": index,
            "caseId": result.get("caseId"),
            "expected": result.get("expected"),
            "status": result.get("status"),
            "score": result.get("score"),
            "judgeScore": judge.get("score"),
            "judgeCorrect": judge.get("correct"),
            "judgeGrounded": judge.get("grounded"),
            "judgeHallucination": judge.get("hallucination"),
            "judgeReason": judge.get("reason"),
            "latencySeconds": result.get("latencySeconds"),
            "question": result.get("question"),
            "answer": result.get("answerText") or result.get("answerPreview") or "",
            "failedChecks": failedChecks,
            "citations": citations,
        }
        jsonlLines.append(json.dumps(logItem, ensure_ascii=False))
        markdown.extend(
            [
                f"## {index:04d} - {result.get('status')} - score {float(result.get('score') or 0):.3f}",
                "",
                f"- Case: `{result.get('caseId')}`",
                f"- Expected source: `{(result.get('expected') or {}).get('documentName')}` p.`{(result.get('expected') or {}).get('page')}` chunk `{(result.get('expected') or {}).get('chunkId')}`",
                f"- Judge score: `{judge.get('score')}`",
                f"- Judge: correct=`{judge.get('correct')}`, grounded=`{judge.get('grounded')}`, hallucination=`{judge.get('hallucination')}`",
                f"- Failed checks: `{', '.join(failedChecks) if failedChecks else 'none'}`",
                f"- Latency: `{float(result.get('latencySeconds') or 0):.2f}s`",
                "",
                "**Question**",
                "",
                str(result.get("question") or ""),
                "",
                "**Expected Source Excerpt**",
                "",
                str((result.get("expected") or {}).get("sourceExcerpt") or ""),
                "",
                "**Answer**",
                "",
                str(result.get("answerText") or result.get("answerPreview") or ""),
                "",
                "**Judge Reason**",
                "",
                str(judge.get("reason") or ""),
                "",
            ]
        )
        if citations:
            markdown.append("**Citations**")
            markdown.append("")
            for citation in citations:
                markdown.append(
                    f"- `{citation['source']}` p.`{citation['page']}` chunk `{citation['chunkId']}` confidence `{citation['confidence']}`"
                )
            markdown.append("")
    (run_dir / "case-log.jsonl").write_text("\n".join(jsonlLines) + ("\n" if jsonlLines else ""), encoding="utf-8")
    (run_dir / "case-log.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
