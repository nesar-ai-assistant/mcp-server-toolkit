"""Tests for mcp_server_toolkit.cli."""

from __future__ import annotations

from mcp_server_toolkit.cli import ServerArgs, parse_server_args


def test_defaults() -> None:
    args = parse_server_args([])
    assert args == ServerArgs(transport="stdio", host="127.0.0.1", port=8000)


def test_parses_streamable_http_flags() -> None:
    args = parse_server_args(
        ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "9100"]
    )
    assert args.transport == "streamable-http"
    assert args.host == "0.0.0.0"
    assert args.port == 9100


def test_rejects_unknown_transport() -> None:
    import pytest

    with pytest.raises(SystemExit):
        parse_server_args(["--transport", "carrier-pigeon"])
