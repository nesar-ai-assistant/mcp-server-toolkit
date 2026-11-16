"""Tool-module discovery from ``pyproject.toml``.

The spectra-mcp-server pattern keeps science code in plain Python
modules under ``tools/``, each exporting its public tool functions via
``__all__``. The generic ``mcp_server/server.py`` wrapper doesn't
hardcode which modules to import -- it reads the list from
``[tool.mcp-server].tool_modules`` in the project's ``pyproject.toml``,
so adding a new tool module is a one-line config change, not a server
code change.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - only hit on Python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]


class ToolDiscoveryError(RuntimeError):
    """Raised when tool modules cannot be located or imported."""


def read_tool_modules(pyproject_path: str | Path = "pyproject.toml") -> list[str]:
    """Read ``[tool.mcp-server].tool_modules`` from a ``pyproject.toml``.

    Args:
        pyproject_path: Path to the ``pyproject.toml`` file to read.

    Returns:
        The list of dotted module paths configured under
        ``tool_modules``. Empty list if the table/key is absent.

    Raises:
        ToolDiscoveryError: If the file does not exist or is not valid
            TOML.
    """
    path = Path(pyproject_path)
    if not path.is_file():
        raise ToolDiscoveryError(f"pyproject.toml not found at {path!s}")

    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:  # pragma: no cover - defensive
        raise ToolDiscoveryError(f"Could not parse {path!s}: {exc}") from exc

    tool_modules = data.get("tool", {}).get("mcp-server", {}).get("tool_modules", [])
    if not isinstance(tool_modules, list):
        raise ToolDiscoveryError(
            "[tool.mcp-server].tool_modules must be a list of module paths"
        )
    return [str(m) for m in tool_modules]


def discover_tool_modules(
    pyproject_path: str | Path = "pyproject.toml",
) -> dict[str, Callable[..., Any]]:
    """Import configured tool modules and collect their ``__all__`` callables.

    For each dotted module path in ``[tool.mcp-server].tool_modules``,
    imports the module and reads its ``__all__`` list; every name in
    ``__all__`` is looked up on the module and, if callable, added to
    the returned mapping (name -> function). Modules without an
    ``__all__`` are skipped with no entries collected (the convention
    is that ``__all__`` is what gates MCP-tool registration).

    Args:
        pyproject_path: Path to the ``pyproject.toml`` to read
            ``tool_modules`` from.

    Returns:
        Mapping of tool function name to the function object, suitable
        for registering with a FastMCP server via ``mcp.tool()``.

    Raises:
        ToolDiscoveryError: If a configured module cannot be imported,
            or a name in ``__all__`` is missing or not callable.
    """
    tools: dict[str, Callable[..., Any]] = {}
    for module_path in read_tool_modules(pyproject_path):
        try:
            module = importlib.import_module(module_path)
        except ImportError as exc:
            raise ToolDiscoveryError(
                f"Could not import tool module {module_path!r}: {exc}"
            ) from exc

        public_names = getattr(module, "__all__", None)
        if not public_names:
            continue

        for name in public_names:
            func = getattr(module, name, None)
            if func is None:
                raise ToolDiscoveryError(
                    f"{module_path}.__all__ lists {name!r}, but no such attribute exists"
                )
            if not callable(func):
                raise ToolDiscoveryError(
                    f"{module_path}.{name} is in __all__ but is not callable"
                )
            tools[name] = func

    return tools
