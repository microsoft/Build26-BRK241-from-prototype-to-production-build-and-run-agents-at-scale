"""Offline smoke tests for the fibey-coordinator agent.

These do NOT import the agent module (``main.py`` pulls in the Microsoft Agent
Framework and raises on a missing ``FOUNDRY_PROJECT_ENDPOINT`` at import time).
Instead they validate the deploy config and that every Python source parses —
enough to catch a broken agent.yaml or a syntax error before deployment.

Run:
    pip install -r requirements-dev.txt
    pytest tests/test_fibey.py
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIBEY = REPO_ROOT / "src" / "fibey-coordinator"


def test_fibey_folder_exists():
    assert FIBEY.is_dir(), f"fibey-coordinator folder missing at {FIBEY}"


def test_fibey_required_files_present():
    for name in ("agent.yaml", "main.py", "requirements.txt", "Dockerfile"):
        assert (FIBEY / name).is_file(), f"fibey-coordinator missing {name}"


def test_fibey_agent_yaml_is_valid():
    yaml = pytest.importorskip("yaml", reason="pyyaml not installed")
    data = yaml.safe_load((FIBEY / "agent.yaml").read_text(encoding="utf-8"))
    assert data.get("kind") == "hosted"
    assert data.get("name") == "fibey-coordinator"
    protocols = {p.get("protocol") for p in data.get("protocols", [])}
    # The Teams/long-running coordinator relies on both protocols.
    assert "responses" in protocols
    assert "activity_protocol" in protocols


@pytest.mark.parametrize("py_file", sorted((REPO_ROOT / "src" / "fibey-coordinator").glob("*.py")), ids=lambda p: p.name)
def test_fibey_python_sources_parse(py_file: Path):
    """Syntax-check every source file without importing (no heavy deps run)."""
    source = py_file.read_text(encoding="utf-8")
    ast.parse(source, filename=str(py_file))
