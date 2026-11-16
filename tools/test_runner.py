
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_NAME = "ai-developer-test-runner:1.0"
ALLOWED_TEST_DIR = PROJECT_ROOT / "generated_tests"
EXAMPLES_DIR = PROJECT_ROOT / "examples"


def run_generated_tests(filename: str, approved: bool = False) -> dict:
    """Execute an approved generated test in a restricted Docker container."""

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
        return {"status": "error", "output": "Invalid test filename."}

    test_file = ALLOWED_TEST_DIR / filename

    if not test_file.is_file() or test_file.is_symlink():
        return {
            "status": "error",
            "output": f"Test file not found or not allowed: {filename}"
        }

    # Initially support only the reviewed calculator module.
    source_file = EXAMPLES_DIR / "calculator.py"

    if not source_file.is_file() or source_file.is_symlink():
        return {
            "status": "error",
            "output": "Approved calculator source file is unavailable."
        }

    container_name = f"ai-test-{uuid.uuid4().hex[:12]}"

    with tempfile.TemporaryDirectory(prefix="ai-test-") as temp_dir:
        staging = Path(temp_dir)
        (staging / "generated_tests").mkdir()
        (staging / "examples").mkdir()

        shutil.copyfile(
            test_file,
            staging / "generated_tests" / filename
        )

        shutil.copyfile(
            source_file,
            staging / "examples" / "calculator.py"
        )

        command = [
            "docker", "run", "--rm",
            "--name", container_name,
            "--network", "none",
            "--read-only",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--memory", "256m",
            "--cpus", "1",
            "--pids-limit", "64",
            "--tmpfs", "/tmp:rw,nosuid,nodev,size=32m",
            "--mount",
            f"type=bind,source={staging},target=/workspace,readonly",
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
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                timeout=15,
                check=False
            )

            return {
                "status": "timeout",
                "output": "Test execution exceeded 60 seconds."
            }

        except FileNotFoundError:
            return {
                "status": "error",
                "output": "Docker CLI was not found."
            }
