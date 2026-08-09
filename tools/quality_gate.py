"""Repository policy checks that need no network or third-party package."""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_STDLIB = {
    "argparse",
    "copy",
    "contextlib",
    "dataclasses",
    "decimal",
    "fractions",
    "hashlib",
    "hmac",
    "html",
    "http",
    "importlib",
    "io",
    "itertools",
    "json",
    "os",
    "pathlib",
    "re",
    "shutil",
    "struct",
    "subprocess",
    "sys",
    "tempfile",
    "textwrap",
    "time",
    "types",
    "typing",
    "unittest",
    "urllib",
    "wsgiref",
    "xml",
    "zlib",
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [
        ROOT / item.decode("utf-8")
        for item in result.stdout.split(b"\0")
        if item
    ]


def check_imports(path: Path) -> list[str]:
    failures: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        module = None
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root not in ALLOWED_STDLIB:
                    failures.append(f"{path.relative_to(ROOT)} imports {root}")
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            module = node.module.split(".", 1)[0]
        if module and module not in ALLOWED_STDLIB:
            failures.append(f"{path.relative_to(ROOT)} imports {module}")
    return failures


def main() -> int:
    failures: list[str] = []
    files = tracked_files()
    relative = {path.relative_to(ROOT).as_posix() for path in files}

    for path in files:
        name = path.name.lower()
        rel = path.relative_to(ROOT).as_posix()
        if name.startswith(".env") or name.endswith((".pem", ".p12", ".key")):
            failures.append(f"secret-shaped tracked path: {rel}")
        if rel.startswith("evidence/staged/"):
            failures.append(f"unreviewed evidence is tracked: {rel}")
        if path.is_symlink():
            failures.append(f"symlink is not allowed: {rel}")

    if any(name in relative for name in {"LICENSE", "LICENSE.md", "LICENSE.txt"}):
        failures.append("license file added before the explicit rights decision")

    runtime_lock = (ROOT / "requirements.lock").read_text(encoding="utf-8")
    runtime_lines = [
        line for line in runtime_lock.splitlines() if line.strip() and not line.startswith("#")
    ]
    if runtime_lines:
        failures.append("runtime dependency lock is not empty")

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if "dependencies = []" not in pyproject:
        failures.append("pyproject runtime dependencies are not explicitly empty")

    for path in (ROOT / "measuretrace").glob("*.py"):
        failures.extend(check_imports(path))
        source = path.read_text(encoding="utf-8").lower().replace(" ", "")
        for forbidden in ("debug=true", "stackpath.bootstrapcdn.com", "bootstrapcdn.com"):
            if forbidden in source:
                failures.append(f"production source contains {forbidden}: {path.name}")

    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    uses = re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, flags=re.MULTILINE)
    for action in uses:
        if re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", action) is None:
            failures.append(f"GitHub Action is not pinned to a 40-character SHA: {action}")
    if "permissions:\n  contents: read" not in workflow:
        failures.append("workflow does not declare read-only contents permission")
    if "persist-credentials: false" not in workflow:
        failures.append("checkout credentials are not explicitly disabled")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(
        f"policy gate passed: {len(files)} tracked files, "
        "stdlib-only runtime, pinned read-only workflow"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
