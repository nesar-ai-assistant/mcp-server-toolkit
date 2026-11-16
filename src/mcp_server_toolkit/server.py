"""Generic FastMCP server wrapper (~70 lines, per the spectra pattern).

This module is intentionally thin: it discovers tool functions via
:mod:`mcp_server_toolkit.discovery`, registers each with a
:class:`fastmcp.FastMCP` instance, and runs it with the transport
selected on the CLI. All science logic lives in the caller's
``tools/`` package, never here.

``fastmcp`` is an optional dependency (``pip install
mcp-server-toolkit[server]``) so that the pure-Python ``tools/``
layer of a server can be imported and unit-tested without pulling in
the MCP/network stack at all.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp_server_toolkit.discovery import discover_tool_modules


def clear_stale_port(port: int, host: str = "127.0.0.1") -> None:
    """Best-effort cleanup of a leftover suspended process on ``port``.

    Local dev loops that restart a streamable-http server frequently
    leave a suspended/zombie process holding the port. This is a
    best-effort, platform-tolerant cleanup: failures are swallowed
    since binding will simply fail loudly afterward if the port is
    still in use for a legitimate reason.
    """
    import contextlib
    import signal
    import subprocess

    with contextlib.suppress(Exception):
        output = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        for pid_str in output.splitlines():
            with contextlib.suppress(ValueError, ProcessLookupError, PermissionError):
                os.kill(int(pid_str), signal.SIGTERM)


def create_server(
    name: str,
    pyproject_path: str | Path = "pyproject.toml",
    **fastmcp_kwargs: Any,
) -> Any:
    """Build a FastMCP server with tools discovered from ``pyproject.toml``.

    Args:
        name: Server name to show to MCP clients.
        pyproject_path: Path to the project's ``pyproject.toml``,
            used to discover ``[tool.mcp-server].tool_modules``.
        **fastmcp_kwargs: Extra keyword arguments forwarded to
            ``FastMCP(...)`` (e.g. ``instructions=``).

    Returns:
        A configured ``fastmcp.FastMCP`` instance with every
        discovered tool function registered.

    Raises:
        ImportError: If ``fastmcp`` is not installed. Install with
            ``pip install mcp-server-toolkit[server]``.
    """
    try:
        from fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - exercised only without extra
        raise ImportError(
            "fastmcp is required to create a server; install with "
            "'pip install mcp-server-toolkit[server]'"
        ) from exc

    if os.environ.get("MCP_PUBLIC") == "1":
        # Disable DNS rebinding protection for tunnel/cloud serving, where
        # the public hostname legitimately differs from the bind host.
        fastmcp_kwargs.setdefault("dns_rebinding_protection", False)

    mcp = FastMCP(name=name, **fastmcp_kwargs)

    tools = discover_tool_modules(pyproject_path)
    for tool_name, func in tools.items():
        mcp.tool(name=tool_name)(func)

    return mcp


def run_server(
    name: str,
    transport: str = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    pyproject_path: str | Path = "pyproject.toml",
    **fastmcp_kwargs: Any,
) -> None:
    """Create and run an MCP server (blocking).

    Args:
        name: Server name to show to MCP clients.
        transport: ``"stdio"`` or ``"streamable-http"``.
        host: Bind host for ``streamable-http``.
        port: Bind port for ``streamable-http``; stale occupants are
            cleared first via :func:`clear_stale_port`.
        pyproject_path: Path to ``pyproject.toml`` for tool discovery.
        **fastmcp_kwargs: Extra keyword arguments forwarded to
            :func:`create_server`.
    """
    mcp = create_server(name, pyproject_path=pyproject_path, **fastmcp_kwargs)

    if transport == "streamable-http":
        clear_stale_port(port, host=host)
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        mcp.run(transport="stdio")
