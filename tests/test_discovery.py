"""Tests for mcp_server_toolkit.discovery."""

from __future__ import annotations

import sys
import types
from collections.abc import Iterator

import pytest

from mcp_server_toolkit.discovery import (
    ToolDiscoveryError,
    discover_tool_modules,
    read_tool_modules,
)


def test_read_tool_modules_missing_file(tmp_path) -> None:
    with pytest.raises(ToolDiscoveryError, match="not found"):
        read_tool_modules(tmp_path / "does-not-exist.toml")


def test_read_tool_modules_absent_key_returns_empty(tmp_path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'x'\n")
    assert read_tool_modules(pyproject) == []


def test_read_tool_modules_returns_configured_list(tmp_path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\nname = 'x'\n\n[tool.mcp-server]\ntool_modules = ['tools', 'extra_tools']\n"
    )
    assert read_tool_modules(pyproject) == ["tools", "extra_tools"]


def test_read_tool_modules_rejects_non_list(tmp_path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.mcp-server]\ntool_modules = 'tools'\n")
    with pytest.raises(ToolDiscoveryError, match="must be a list"):
        read_tool_modules(pyproject)


@pytest.fixture()
def fake_tool_module() -> Iterator[types.ModuleType]:
    """Register a fake importable module with one tool function."""
    module = types.ModuleType("fake_mcp_tools")

    def do_thing(x: int) -> int:
        """Double x."""
        return x * 2

    module.do_thing = do_thing  # type: ignore[attr-defined]
    module.__all__ = ["do_thing"]  # type: ignore[attr-defined]
    sys.modules["fake_mcp_tools"] = module
    yield module
    del sys.modules["fake_mcp_tools"]


def test_discover_tool_modules_collects_all_callables(tmp_path, fake_tool_module) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.mcp-server]\ntool_modules = ['fake_mcp_tools']\n")

    tools = discover_tool_modules(pyproject)

    assert set(tools) == {"do_thing"}
    assert tools["do_thing"](21) == 42


def test_discover_tool_modules_missing_module_raises(tmp_path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.mcp-server]\ntool_modules = ['does_not_exist_mod']\n")

    with pytest.raises(ToolDiscoveryError, match="Could not import"):
        discover_tool_modules(pyproject)


def test_discover_tool_modules_bad_all_entry_raises(tmp_path) -> None:
    module = types.ModuleType("fake_mcp_tools_bad")
    module.__all__ = ["missing_name"]  # type: ignore[attr-defined]
    sys.modules["fake_mcp_tools_bad"] = module
    try:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.mcp-server]\ntool_modules = ['fake_mcp_tools_bad']\n")
        with pytest.raises(ToolDiscoveryError, match="no such attribute"):
            discover_tool_modules(pyproject)
    finally:
        del sys.modules["fake_mcp_tools_bad"]
