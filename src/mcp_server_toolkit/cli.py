"""Shared argparse CLI for MCP server entry points.

Every server built on this toolkit exposes the same small set of
flags from its ``mcp_server/cli.py`` / ``__main__.py``:
``--transport {stdio,streamable-http} --host --port``. This module
provides a single parser builder so that contract stays consistent
across servers instead of being hand-copied and drifting.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


@dataclass(frozen=True)
class ServerArgs:
    """Parsed CLI arguments for an MCP server process."""

    transport: str
    host: str
    port: int


def build_arg_parser(prog: str | None = None) -> argparse.ArgumentParser:
    """Build the standard MCP server argument parser.

    Args:
        prog: Optional program name to show in ``--help`` output
            (defaults to ``sys.argv[0]`` if omitted).

    Returns:
        A configured :class:`argparse.ArgumentParser` with
        ``--transport``, ``--host``, and ``--port`` options.
    """
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Run an MCP science server (stdio or streamable-http transport).",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport to serve over. 'stdio' for local Claude Code / agent clients, "
        "'streamable-http' for networked/tunnel deployments. Default: stdio.",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host to bind for streamable-http transport. Default: {DEFAULT_HOST}.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to bind for streamable-http transport. Default: {DEFAULT_PORT}.",
    )
    return parser


def parse_server_args(argv: list[str] | None = None, prog: str | None = None) -> ServerArgs:
    """Parse CLI args into a :class:`ServerArgs` value object.

    Args:
        argv: Argument list to parse (defaults to ``sys.argv[1:]``).
        prog: Optional program name for ``--help`` output.

    Returns:
        A populated :class:`ServerArgs`.
    """
    parser = build_arg_parser(prog=prog)
    namespace = parser.parse_args(argv)
    return ServerArgs(transport=namespace.transport, host=namespace.host, port=namespace.port)
