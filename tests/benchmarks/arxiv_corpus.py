#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from resource_guard import ResourceGuard, ResourceGuardError, ResourceThresholds  # noqa: E402

CORPUS_DIR = ROOT / "tests" / "benchmarks" / "corpus" / "arxiv"
ARXIV_API = "https://export.arxiv.org/api/query"
DEFAULT_QUERY = "cat:cs.AI OR cat:cs.CL OR cat:cs.LG OR cat:cs.IR"
USER_AGENT = "facespeed-rag-benchmark/0.1 (local benchmark; contact: local)"
ATOM = "{http://www.w3.org/2005/Atom}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest an open arXiv PDF corpus for RAG benchmarks.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    download = subparsers.add_parser("download")
    download.add_argument("--limit", type=int, required=True)
    download.add_argument("--query", default=DEFAULT_QUERY)
    download.add_argument("--start", type=int, default=0)
    download.add_argument("--delay", type=float, default=3.0)
    download.add_argument("--max-mb", type=float, default=20.0)

    direct = subparsers.add_parser("download-direct")
    direct.add_argument("--limit", type=int, required=True)
    direct.add_argument("--prefix", default="2605")
    direct.add_argument("--start-number", type=int, default=22774)
    direct.add_argument("--delay", type=float, default=3.0)
    direct.add_argument("--max-mb", type=float, default=20.0)

    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("--api-base", default="http://127.0.0.1:6320")
    ingest.add_argument("--limit", type=int, default=0, help="0 means ingest all downloaded PDFs.")
    ingest.add_argument("--max-new", type=int, default=0, help="0 means no cap; otherwise stop after this many new upload attempts.")
    ingest.add_argument("--retry-failures", action="store_true", help="Retry PDFs that already have a failed result in ingest-results.json.")
    ingest.add_argument("--only-ids", default="", help="Comma-separated arXiv IDs to ingest/retry.")
    ingest.add_argument("--delay", type=float, default=0.25)
    ingest.add_argument("--language", default="en-US")
    ingest.add_argument("--ram-min-free-percent", type=float, default=10.0)
    ingest.add_argument("--gpu-min-free-vram-percent", type=float, default=10.0)
    ingest.add_argument("--disk-min-free-percent", type=float, default=10.0)
    ingest.add_argument("--request-timeout", type=float, default=360.0)
    args = parser.parse_args()

    if args.command == "download":
        download_corpus(args.limit, args.query, args.start, args.delay, args.max_mb)
    elif args.command == "download-direct":
        download_direct_corpus(args.limit, args.prefix, args.start_number, args.delay, args.max_mb)
    elif args.command == "ingest":
        guard = ResourceGuard(
            ROOT,
            ResourceThresholds(
                ram_min_free_percent=args.ram_min_free_percent,
                gpu_min_free_vram_percent=args.gpu_min_free_vram_percent,
                disk_min_free_percent=args.disk_min_free_percent,
            ),
        )
        only_ids = {item.strip() for item in args.only_ids.split(",") if item.strip()}
        ingest_corpus(args.api_base, args.limit, args.max_new, args.retry_failures, args.delay, args.language, guard, only_ids, args.request_timeout)


def download_corpus(limit: int, query: str, start: int, delay: float, max_mb: float) -> None:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = CORPUS_DIR / "metadata.json"
    metadata = load_metadata(metadata_path)
    existing_ids = {item["arxivId"] for item in metadata}
    fetched = 0
    cursor = start
    while fetched < limit:
        entries = query_arxiv(query, cursor, min(100, limit - fetched + len(existing_ids)))
        if not entries:
            break
        for entry in entries:
            arxiv_id = entry["arxivId"]
            if arxiv_id in existing_ids:
                continue
            pdf_path = CORPUS_DIR / f"{safe_id(arxiv_id)}.pdf"
            print(f"download {arxiv_id} -> {pdf_path.relative_to(ROOT)}")
            ok, reason, size = download_pdf(entry["pdfUrl"], pdf_path, max_mb)
            if ok:
                entry.update({"path": str(pdf_path.relative_to(ROOT)), "bytes": size, "downloadedAt": now()})
                metadata.append(entry)
                existing_ids.add(arxiv_id)
                fetched += 1
                write_metadata(metadata_path, metadata)
            else:
                print(f"skip {arxiv_id}: {reason}")
            if fetched >= limit:
                break
            time.sleep(delay)
        cursor += len(entries)
    write_metadata(metadata_path, metadata)
    print(f"downloaded={fetched} total={len(metadata)} corpus={CORPUS_DIR.relative_to(ROOT)}")


def download_direct_corpus(limit: int, prefix: str, start_number: int, delay: float, max_mb: float) -> None:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = CORPUS_DIR / "metadata.json"
    metadata = load_metadata(metadata_path)
    existing_ids = {item["arxivId"] for item in metadata}
    fetched = 0
    current = start_number
    misses = 0
    while fetched < limit and misses < 300:
        arxiv_id = f"{prefix}.{current:05d}v1"
        current -= 1
        if arxiv_id in existing_ids:
            continue
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        pdf_path = CORPUS_DIR / f"{safe_id(arxiv_id)}.pdf"
        print(f"download {arxiv_id} -> {pdf_path.relative_to(ROOT)}", flush=True)
        try:
            ok, reason, size = download_pdf(pdf_url, pdf_path, max_mb)
        except urllib.error.HTTPError as exc:
            misses += 1
            print(f"skip {arxiv_id}: HTTP {exc.code}", flush=True)
            time.sleep(delay)
            continue
        if ok:
            metadata.append(
                {
                    "arxivId": arxiv_id,
                    "title": f"arXiv {arxiv_id}",
                    "summary": "",
                    "published": "",
                    "pdfUrl": pdf_url,
                    "path": str(pdf_path.relative_to(ROOT)),
                    "bytes": size,
                    "downloadedAt": now(),
                }
            )
            existing_ids.add(arxiv_id)
            fetched += 1
            misses = 0
            write_metadata(metadata_path, metadata)
        else:
            misses += 1
            print(f"skip {arxiv_id}: {reason}", flush=True)
        time.sleep(delay)
    write_metadata(metadata_path, metadata)
    print(f"downloaded={fetched} total={len(metadata)} corpus={CORPUS_DIR.relative_to(ROOT)}", flush=True)


def ingest_corpus(
    api_base: str,
    limit: int,
    max_new: int,
    retry_failures: bool,
    delay: float,
    language: str,
    guard: ResourceGuard,
    only_ids: set[str] | None = None,
    request_timeout: float = 360.0,
) -> None:
    metadata = load_metadata(CORPUS_DIR / "metadata.json")
    selected = metadata[:limit] if limit else metadata
    if only_ids:
        selected = [item for item in selected if item["arxivId"] in only_ids]
    report_path = CORPUS_DIR / "ingest-results.json"
    result_by_id: dict[str, dict[str, Any]] = {}
    if report_path.exists():
        previous_body = json.loads(report_path.read_text(encoding="utf-8"))
        result_by_id = {result["arxivId"]: result for result in previous_body.get("results", []) if result.get("arxivId")}

    def checkpoint() -> None:
        ordered = [result_by_id[item["arxivId"]] for item in metadata if item["arxivId"] in result_by_id]
        extras = [result for arxiv_id, result in result_by_id.items() if arxiv_id not in {item["arxivId"] for item in metadata}]
        results = [*ordered, *extras]
        report_path.write_text(json.dumps({"createdAt": now(), "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")

    existing_by_filename = list_existing_documents(api_base)
    new_attempts = 0
    for index, item in enumerate(selected, start=1):
        try:
            guard.assert_safe(f"before-ingest-{index:04d}")
        except ResourceGuardError as exc:
            print(str(exc), flush=True)
            break
        if result_by_id.get(item["arxivId"], {}).get("ok"):
            print(f"ingest {index}/{len(selected)} skip {item['arxivId']} already ok", flush=True)
            continue
        if item["arxivId"] in result_by_id and not retry_failures:
            print(f"ingest {index}/{len(selected)} skip {item['arxivId']} previous failure", flush=True)
            continue
        if max_new and new_attempts >= max_new:
            print(f"ingest paused after {new_attempts} new upload attempts; rerun to continue", flush=True)
            break
        new_attempts += 1
        path = ROOT / item["path"]
        if not path.exists():
            result_by_id[item["arxivId"]] = {"arxivId": item["arxivId"], "ok": False, "error": "missing file"}
            checkpoint()
            continue
        existing = existing_by_filename.get(path.name)
        if existing:
            print(f"ingest {index}/{len(selected)} reconcile {path.name} chunks={existing.get('chunkCount')}", flush=True)
            result_by_id[item["arxivId"]] = {
                "arxivId": item["arxivId"],
                "ok": True,
                "documentId": existing.get("id"),
                "chunkCount": existing.get("chunkCount"),
                "reconciled": True,
            }
            checkpoint()
            continue
        url = f"{api_base.rstrip()}/api/documents?{urllib.parse.urlencode({'filename': path.name, 'language': language})}"
        request = urllib.request.Request(
            url,
            data=path.read_bytes(),
            method="POST",
            headers={"Content-Type": "application/pdf", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=request_timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
            print(f"ingest {index}/{len(selected)} ok {path.name} chunks={body.get('chunkCount')}", flush=True)
            result_by_id[item["arxivId"]] = {"arxivId": item["arxivId"], "ok": True, "documentId": body.get("id"), "chunkCount": body.get("chunkCount")}
            checkpoint()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            print(f"ingest {index}/{len(selected)} fail {path.name}: HTTP {exc.code} {detail}", flush=True)
            result_by_id[item["arxivId"]] = {"arxivId": item["arxivId"], "ok": False, "error": f"HTTP {exc.code}: {detail}"}
            checkpoint()
        except Exception as exc:  # noqa: BLE001
            print(f"ingest {index}/{len(selected)} fail {path.name}: {exc}", flush=True)
            result_by_id[item["arxivId"]] = {"arxivId": item["arxivId"], "ok": False, "error": str(exc)}
            checkpoint()
        try:
            guard.assert_safe(f"after-ingest-{index:04d}")
        except ResourceGuardError as exc:
            print(str(exc), flush=True)
            break
        time.sleep(delay)
    checkpoint()
    ok_count = sum(1 for result in result_by_id.values() if result["ok"])
    print(f"ingested={ok_count}/{len(result_by_id)} report={report_path.relative_to(ROOT)}")


def list_existing_documents(api_base: str) -> dict[str, dict[str, Any]]:
    url = f"{api_base.rstrip('/')}/api/documents"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"warning: cannot list existing documents for reconciliation: {exc}", flush=True)
        return {}
    if not isinstance(body, list):
        return {}
    return {item["filename"]: item for item in body if isinstance(item, dict) and item.get("filename")}


def query_arxiv(query: str, start: int, max_results: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    request = urllib.request.Request(f"{ARXIV_API}?{params}", headers={"User-Agent": USER_AGENT})
    xml = b""
    for attempt in range(1, 5):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                xml = response.read()
            break
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 4:
                raise
            wait_seconds = 30 * attempt
            print(f"arXiv API rate limited at start={start}; waiting {wait_seconds}s before retry {attempt + 1}/4")
            time.sleep(wait_seconds)
    root = ET.fromstring(xml)
    entries = []
    for entry in root.findall(f"{ATOM}entry"):
        raw_id = text(entry, "id").rsplit("/", 1)[-1]
        pdf_url = ""
        for link in entry.findall(f"{ATOM}link"):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib.get("href", "")
                break
        if not pdf_url:
            pdf_url = f"https://arxiv.org/pdf/{raw_id}.pdf"
        entries.append(
            {
                "arxivId": raw_id,
                "title": " ".join(text(entry, "title").split()),
                "summary": " ".join(text(entry, "summary").split()),
                "published": text(entry, "published"),
                "pdfUrl": pdf_url,
            }
        )
    return entries


def download_pdf(url: str, path: Path, max_mb: float) -> tuple[bool, str, int]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    body = b""
    content_type = ""
    for attempt in range(1, 5):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                content_type = response.headers.get("content-type", "")
                body = response.read()
            break
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 4:
                raise
            wait_seconds = 30 * attempt
            print(f"PDF download rate limited for {url}; waiting {wait_seconds}s before retry {attempt + 1}/4")
            time.sleep(wait_seconds)
    if "pdf" not in content_type.lower() and not body.startswith(b"%PDF"):
        return False, f"not a PDF ({content_type})", len(body)
    if len(body) > max_mb * 1024 * 1024:
        return False, f"too large {len(body)} bytes", len(body)
    path.write_bytes(body)
    return True, "", len(body)


def text(entry: ET.Element, name: str) -> str:
    found = entry.find(f"{ATOM}{name}")
    return "" if found is None or found.text is None else found.text


def safe_id(arxiv_id: str) -> str:
    return arxiv_id.replace("/", "_").replace(".", "_")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_metadata(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def write_metadata(path: Path, metadata: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
