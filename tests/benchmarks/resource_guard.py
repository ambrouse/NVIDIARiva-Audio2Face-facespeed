from __future__ import annotations

import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ResourceGuardError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResourceThresholds:
    ram_min_free_percent: float = 10.0
    gpu_min_free_vram_percent: float = 10.0
    disk_min_free_percent: float = 10.0


class ResourceGuard:
    def __init__(self, root: Path, thresholds: ResourceThresholds) -> None:
        self.root = root
        self.thresholds = thresholds
        self.samples: list[dict[str, Any]] = []

    def assert_safe(self, label: str) -> dict[str, Any]:
        sample = self.snapshot(label)
        self.samples.append(sample)
        failures = []
        ram = sample.get("ram") or {}
        gpu = sample.get("gpu") or {}
        disk = sample.get("disk") or {}
        if ram and ram["freePercent"] < self.thresholds.ram_min_free_percent:
            failures.append(f"RAM free {ram['freePercent']:.1f}% < {self.thresholds.ram_min_free_percent:.1f}%")
        if gpu and gpu["freeVramPercent"] < self.thresholds.gpu_min_free_vram_percent:
            failures.append(f"VRAM free {gpu['freeVramPercent']:.1f}% < {self.thresholds.gpu_min_free_vram_percent:.1f}%")
        if disk and disk["freePercent"] < self.thresholds.disk_min_free_percent:
            failures.append(f"disk free {disk['freePercent']:.1f}% < {self.thresholds.disk_min_free_percent:.1f}%")
        if failures:
            sample["ok"] = False
            sample["reason"] = "; ".join(failures)
            raise ResourceGuardError(f"Resource guard stopped at {label}: {sample['reason']}")
        sample["ok"] = True
        return sample

    def snapshot(self, label: str) -> dict[str, Any]:
        return {
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "label": label,
            "ram": read_ram(),
            "gpu": read_gpu(),
            "disk": read_disk(self.root),
        }


def read_ram() -> dict[str, Any]:
    values: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0].endswith(":"):
                values[parts[0].rstrip(":")] = int(parts[1])
    except OSError:
        return {}
    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", 0)
    if total <= 0:
        return {}
    return {
        "totalMiB": round(total / 1024, 1),
        "availableMiB": round(available / 1024, 1),
        "freePercent": (available / total) * 100,
    }


def read_gpu() -> dict[str, Any]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            encoding="utf-8",
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    if result.returncode != 0 or not result.stdout.strip():
        return {}
    line = result.stdout.strip().splitlines()[0]
    parts = [part.strip() for part in line.split(",")]
    if len(parts) < 6:
        return {}
    total = float(parts[2])
    used = float(parts[3])
    free = float(parts[4])
    return {
        "index": parts[0],
        "name": parts[1],
        "totalMiB": total,
        "usedMiB": used,
        "freeMiB": free,
        "freeVramPercent": (free / total) * 100 if total else 0.0,
        "utilizationPercent": float(parts[5]),
    }


def read_disk(root: Path) -> dict[str, Any]:
    usage = shutil.disk_usage(root)
    return {
        "totalMiB": round(usage.total / 1024 / 1024, 1),
        "freeMiB": round(usage.free / 1024 / 1024, 1),
        "freePercent": (usage.free / usage.total) * 100 if usage.total else 0.0,
    }


def start_resource_monitor(
    guard: ResourceGuard,
    abort_event: threading.Event,
    stop_event: threading.Event,
    interval_seconds: float,
) -> threading.Thread:
    def monitor() -> None:
        while not stop_event.wait(interval_seconds):
            try:
                guard.assert_safe("background-monitor")
            except ResourceGuardError:
                abort_event.set()
                return

    thread = threading.Thread(target=monitor, name="benchmark-resource-monitor", daemon=True)
    thread.start()
    return thread
