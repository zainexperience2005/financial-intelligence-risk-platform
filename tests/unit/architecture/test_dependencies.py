"""Architecture dependency rules."""

import ast
from pathlib import Path


def test_kit_does_not_import_app() -> None:
    """Reusable kit code must remain independent of financial app code."""
    violations: list[str] = []

    for path in Path("src/kit").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (
                node.module == "app" or (node.module or "").startswith("app.")
            ):
                violations.append(f"{path}:{node.lineno}")
            elif isinstance(node, ast.Import) and any(
                alias.name == "app" or alias.name.startswith("app.")
                for alias in node.names
            ):
                violations.append(f"{path}:{node.lineno}")

    assert not violations, f"kit -> app dependency violations: {violations}"
