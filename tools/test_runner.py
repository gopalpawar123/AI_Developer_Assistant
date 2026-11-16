
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_NAME = "ai-developer-test-runner:1.0"
ALLOWED_TEST_DIR = PROJECT_ROOT / "generated_tests"
EXAMPLES_DIR = PROJECT_ROOT / "examples"

ALLOWED_SOURCE_EXTENSIONS = {".py"}


def validate_source_path(source_path: str):
    """Validate a source path inside the approved examples directory."""

    if not isinstance(source_path, str) or not source_path.strip():
        return None

    normalized = source_path.replace("\\", "/")

    if Path(normalized).is_absolute():
        return None

    if ":" in normalized:
        return None

    relative_path = Path(normalized)

    if ".." in relative_path.parts:
        return None

    source_file = (PROJECT_ROOT / relative_path).resolve()
    examples_root = EXAMPLES_DIR.resolve()

    if not source_file.is_relative_to(examples_root):
        return None

    if source_file.suffix not in ALLOWED_SOURCE_EXTENSIONS:
        return None

    # Reject symlinks, including symlinked parent directories.
    current = PROJECT_ROOT
    for part in relative_path.parts:
        current = current / part
        if current.is_symlink():
            return None

    if not source_file.is_file():
        return None

    return source_file


def run_generated_tests(
    filename: str,
    approved: bool = False,
    source_path: str = "examples/calculator.py"
) -> dict:
    """Execute approved generated tests in a restricted Docker container."""

    if not approved:
        return {
            "status": "rejected",
            "output": "User approval is required before executing tests."
        }

    if (
        not isinstance(filename, str)
        or Path(filename).name != filename
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

    if not test_file.is_file() or test_file.is_symlink():
        return {
            "status": "error",
            "output": f"Test file not found or not allowed: {filename}"
        }

    source_file = validate_source_path(source_path)

    if source_file is None:
        return {
            "status": "error",
            "output": f"Invalid or unavailable source file: {source_path}"
        }

    source_relative = source_file.relative_to(PROJECT_ROOT)

    container_name = f"ai-test-{uuid.uuid4().hex[:12]}"

    with tempfile.TemporaryDirectory(prefix="ai-test-") as temp_dir:
        staging = Path(temp_dir)

        test_destination = staging / "generated_tests" / filename
        test_destination.parent.mkdir(parents=True, exist_ok=True)

        source_destination = staging / source_relative
        source_destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.copyfile(test_file, test_destination)
        shutil.copyfile(source_file, source_destination)

        # Support importing modules from the examples package.
        package_dir = source_destination.parent
        while package_dir != staging:
            if package_dir != staging / "generated_tests":
                (package_dir / "__init__.py").touch(exist_ok=True)
            package_dir = package_dir.parent

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
            try:
                subprocess.run(
                    ["docker", "rm", "-f", container_name],
                    capture_output=True,
                    timeout=15,
                    check=False
                )
            except (OSError, subprocess.TimeoutExpired):
                pass

            return {
                "status": "timeout",
                "output": "Test execution exceeded 60 seconds."
            }

        except FileNotFoundError:
            return {
                "status": "error",
                "output": "Docker CLI was not found."
            }
