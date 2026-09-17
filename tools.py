from pathlib import Path
import subprocess

ROOT = Path("target")


def read_file(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    (ROOT / path).write_text(content, encoding="utf-8")
    return "File written successfully."


def run_tests() -> str:
    result = subprocess.run(
        ["pytest", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    return result.stdout + result.stderr