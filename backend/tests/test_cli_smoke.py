import subprocess
import sys


def test_cli_fake_smoke():
    result = subprocess.run([sys.executable, "-m", "foresight.ui.demo_cli", "--fake", "--pybullet-direct"], text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "Scene objects" in result.stdout
    assert "Parser output" in result.stdout
    assert "Safety decision" in result.stdout
