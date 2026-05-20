from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "scripts" / "setup.sh"


def testSetupScriptHasRequiredModes() -> None:
    content = SETUP.read_text(encoding="utf-8")
    for mode in [
        "--auto",
        "--check",
        "--check-nvidia",
        "--check-ports",
        "--check-resources",
        "--check-gpu-light",
        "--check-docker-space",
        "--dry-run-nvidia-full",
        "--dry-run-containers",
        "--install",
        "--install-ngc",
        "--install-riva",
        "--start-riva",
        "--check-riva",
        "--check-a2f",
        "--start-services",
        "--full",
        "--nvidia-full",
    ]:
        assert mode in content


def testSetupScriptLogsToSetupLog() -> None:
    content = SETUP.read_text(encoding="utf-8")
    assert "logs/setup" in content
    assert "setup.log" in content


def testSetupScriptDoesNotForceNvidiaInstall() -> None:
    content = SETUP.read_text(encoding="utf-8")
    assert "requires NVIDIA NGC assets" in content
    assert "NGC_RIVA_QUICKSTART_RESOURCE" in content
    assert "ngc config set" in content
    assert "rm -rf" not in content


def testSetupScriptAvoidsAudio2FacePathFalsePositive() -> None:
    content = SETUP.read_text(encoding="utf-8")
    assert "pgrep -x audio2face" in content
    assert "pgrep -fa audio2face" not in content
    assert "pgrep -fa Audio2Face" not in content


def testSetupScriptDoesNotUseBroadProcessKillCommands() -> None:
    content = SETUP.read_text(encoding="utf-8")
    for unsafe in ["pkill", "killall", "fuser -k", "docker system prune"]:
        assert unsafe not in content


def testSetupScriptHasResourceThresholds() -> None:
    content = SETUP.read_text(encoding="utf-8")
    for name in [
        "RESOURCE_RESERVE_PERCENT",
        "GPU_MIN_FREE_VRAM_PERCENT",
        "RAM_MIN_FREE_PERCENT",
        "DISK_MIN_FREE_PERCENT",
        "Committed_AS",
        "CommitLimit",
    ]:
        assert name in content


def testSetupScriptCheckModesAreReadOnly() -> None:
    content = SETUP.read_text(encoding="utf-8")
    dry_run_start = content.index("run_dry_run_nvidia_full()")
    dry_run_end = content.index("check_ngc", dry_run_start)
    dry_run_body = content[dry_run_start:dry_run_end]
    assert "docker run" not in dry_run_body
    assert "docker pull" not in dry_run_body
    assert "docker volume prune" not in dry_run_body
    assert "download_riva_quickstart" not in dry_run_body
    assert "start_riva" not in dry_run_body


def testSetupScriptContainerDryRunIsScoped() -> None:
    content = SETUP.read_text(encoding="utf-8")
    for expected in [
        "facespeed-riva",
        "facespeed-audio2face",
        "com.facespeed.project=NVIDIARiva-Audio2Face-facespeed",
        "127.0.0.1:${port}",
        "--restart no",
        "CONTAINER_MEMORY_LIMIT",
        "CONTAINER_CPU_LIMIT",
        "GPU_DEVICE_FLAG",
    ]:
        assert expected in content


def testSetupScriptDoesNotStartContainersInDryRunDispatcher() -> None:
    content = SETUP.read_text(encoding="utf-8")
    dispatcher_start = content.index("--dry-run-containers)")
    dispatcher_body = content[dispatcher_start:content.index("--install)", dispatcher_start)]
    assert "run_container_dry_run" in dispatcher_body
    assert "docker run" not in dispatcher_body
    assert "docker pull" not in dispatcher_body
    assert "docker stop" not in dispatcher_body
