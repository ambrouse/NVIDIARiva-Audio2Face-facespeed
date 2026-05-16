from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "scripts" / "setup.sh"


def testSetupScriptHasRequiredModes() -> None:
    content = SETUP.read_text(encoding="utf-8")
    for mode in [
        "--check",
        "--check-nvidia",
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
    assert "rm -rf" not in content
