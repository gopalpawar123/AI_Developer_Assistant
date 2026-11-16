
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_NAME = "ai-developer-test-runner:1.0"
ALLOWED_TEST_DIR = PROJECT_ROOT / "generated_tests"


def run_generated_tests(filename: str, approved: bool = False) -> dict:
    """Run an approved generated pytest file in Docker."""

    if not approved:
        return {
            "status": "rejected",
            "output": "User approval is required before executing tests."
        }

    if (
        Path(filename).name != filename
        or "/" in filename
        or "\\" in filename
        or not filename.startswith("test_")
        or not filename.endswith(".py")
    ):
        return {
            "status": "error",
            "output": "Invalid test filename."
        }

    test_file = ALLOWED_TEST_DIR / filename

    if not test_file.is_file():
        return {
            "status": "error",
            "output": f"Test file not found: {filename}"
        }

    command = [
        "docker", "run", "--rm",
        "--network", "none",
        "--read-only",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--memory", "256m",
        "--cpus", "1",
        "--pids-limit", "64",
        "--tmpfs", "/tmp:rw,nosuid,nodev,size=32m",
        "--mount",
        f"type=bind,source={PROJECT_ROOT / 'examples'},target=/workspace/examples,readonly",
        "--mount",
        f"type=bind,source={ALLOWED_TEST_DIR},target=/workspace/generated_tests,readonly",
        IMAGE_NAME,
        "python", "-m", "pytest",
        "-p", "no:cacheprovider",
        "-o", "addopts=",
        "--basetemp=/tmp/pytest-temp",
        f"generated_tests/{filename}",
        "-v"
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            check=False
        )

        return {
            "status": "passed" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "output": result.stdout + result.stderr
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "output": "Test execution exceeded 60 seconds."
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "output": "Docker CLI was not found."
        }
