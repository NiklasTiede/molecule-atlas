import sys
import tomllib
from pathlib import Path
from typing import TypeIs, cast

REPO_ROOT = Path(__file__).parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"


def _is_string_object_dict(value: object) -> TypeIs[dict[str, object]]:
    if not isinstance(value, dict):
        return False
    mapping = cast(dict[object, object], value)
    return all(isinstance(key, str) for key in mapping)


def _table(value: object, key: str) -> dict[str, object]:
    assert _is_string_object_dict(value)
    nested = value.get(key)
    assert _is_string_object_dict(nested)
    return nested


def _toml(path: Path) -> dict[str, object]:
    parsed: object = tomllib.loads(path.read_text(encoding="utf-8"))
    assert _is_string_object_dict(parsed)
    return parsed


def test_python_version_is_aligned_across_tooling() -> None:
    python_version = (REPO_ROOT / ".python-version").read_text(encoding="utf-8").strip()
    major, minor = (int(part) for part in python_version.split("."))
    next_minor = f"{major}.{minor + 1}"

    pyproject = _toml(BACKEND_ROOT / "pyproject.toml")
    project = _table(pyproject, "project")
    tooling = _table(pyproject, "tool")
    pyright = _table(tooling, "pyright")
    ruff = _table(tooling, "ruff")
    lockfile = _toml(BACKEND_ROOT / "uv.lock")

    assert sys.version_info[:2] == (major, minor)
    assert project["requires-python"] == f">={python_version},<{next_minor}"
    assert lockfile["requires-python"] == f"=={python_version}.*"
    assert pyright["pythonVersion"] == python_version
    assert ruff["target-version"] == f"py{major}{minor}"
    assert f"python{python_version}-" in (BACKEND_ROOT / "Dockerfile").read_text(encoding="utf-8")


def test_ci_runs_required_repository_gates() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    required_commands = (
        "uv sync --frozen --dev",
        "uv run ruff format --check .",
        "uv run ruff check .",
        "uv run pyright",
        "uv run pytest",
        "npm ci",
        "npm run generate:api",
        "npm run lint",
        "npm test",
        "npm run build",
        "npm run e2e",
        "make container-config-test",
        "make container-smoke",
    )

    missing_commands = tuple(command for command in required_commands if command not in workflow)
    assert missing_commands == ()
