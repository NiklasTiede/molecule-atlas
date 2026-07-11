import ast
from pathlib import Path

APP_ROOT = Path(__file__).parents[1] / "app"
CORE_ROOT = Path(__file__).parents[1] / "core" / "src" / "molecule_atlas"

_ALLOWED_APP_IMPORTS: dict[str, frozenset[str]] = {
    "root": frozenset(),
    "models": frozenset({"models"}),
    "chem": frozenset({"chem", "models"}),
    "adapters": frozenset({"adapters", "models"}),
    "services": frozenset({"services", "adapters", "chem", "models"}),
    "application": frozenset({"application", "models"}),
    "infrastructure": frozenset({"application", "infrastructure"}),
    "api": frozenset({"api", "application", "infrastructure", "services", "models"}),
    "main": frozenset({"api", "models"}),
}

_EXTERNAL_IMPORT_OWNERS: dict[str, frozenset[str]] = {
    "fastapi": frozenset({"api", "main"}),
    "numpy": frozenset({"chem"}),
    "pandas": frozenset({"adapters"}),
    "pydantic": frozenset({"application", "models"}),
    "rdkit": frozenset({"chem"}),
    "sklearn": frozenset({"services"}),
}


def _area(path: Path) -> str:
    relative = path.relative_to(APP_ROOT)
    if len(relative.parts) == 1:
        return "main" if relative.name == "main.py" else "root"
    return relative.parts[0]


def _imported_modules(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            if node.module == "app":
                modules.extend(f"app.{alias.name}" for alias in node.names)
            elif node.module is not None:
                modules.append(node.module)
    return tuple(modules)


def test_backend_imports_follow_module_boundaries() -> None:
    violations: list[str] = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        importer = _area(path)
        allowed_app_imports = _ALLOWED_APP_IMPORTS[importer]
        for imported_module in _imported_modules(path):
            parts = imported_module.split(".")
            root = parts[0]
            if root == "app" and len(parts) > 1 and parts[1] not in allowed_app_imports:
                violations.append(
                    f"{path.relative_to(APP_ROOT)}: {importer} cannot import {parts[1]}"
                )
            owners = _EXTERNAL_IMPORT_OWNERS.get(root)
            if owners is not None and importer not in owners:
                violations.append(
                    f"{path.relative_to(APP_ROOT)}: only {sorted(owners)} may import {root}"
                )

    assert violations == []


def test_portable_core_has_no_application_or_infrastructure_imports() -> None:
    forbidden_roots = frozenset(
        {
            "app",
            "fastapi",
            "kubernetes",
            "numpy",
            "pandas",
            "rdkit",
            "sklearn",
            "sqlalchemy",
            "torch",
        }
    )
    violations: list[str] = []
    for path in sorted(CORE_ROOT.rglob("*.py")):
        for imported_module in _imported_modules(path):
            root = imported_module.split(".")[0]
            if root in forbidden_roots:
                violations.append(f"{path.relative_to(CORE_ROOT)} imports forbidden {root}")

    assert violations == []
