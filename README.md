# mcp-server-toolkit

Shared scaffolding for building MCP ("Model Context Protocol") servers
around scientific Python code, extracted from the pattern Nesar
converged on in [`HEP-KE/spectra-mcp-server`](https://github.com/HEP-KE/spectra-mcp-server)
(`dispatch` branch).

**Core idea:** the science code stays in usual Python. The MCP wrapper
only publishes it. Tool functions are plain, type-hinted, docstring'd
Python callables that are independently importable and testable —
`mcp_server_toolkit` turns a `tools/` package into a running MCP server
with almost no boilerplate.

## Install

```bash
pip install mcp-server-toolkit            # core: ArtifactResult, discovery, cli
pip install "mcp-server-toolkit[server]"  # + fastmcp, for actually running a server
```

## What's in the box

| Module | Purpose |
|---|---|
| `mcp_server_toolkit.artifact.ArtifactResult` | Uniform `(status, files, message, metadata)` return contract for every tool. Arrays/plots travel as file paths, never through agent context. |
| `mcp_server_toolkit.discovery.discover_tool_modules` | Reads `[tool.mcp-server].tool_modules` from `pyproject.toml`, imports each module, and collects every name in its `__all__` as a tool function. |
| `mcp_server_toolkit.cli.build_arg_parser` / `parse_server_args` | Standard `--transport {stdio,streamable-http} --host --port` CLI shared across servers. |
| `mcp_server_toolkit.publish.publish_outputs` | Decorator that rewrites local `OUTPUT_ROOT`-relative file paths in a tool's result to `ARTIFACT_URL` URLs, for hosted/tunnel deployments. No-op when those env vars aren't set. |
| `mcp_server_toolkit.server.create_server` / `run_server` | ~70-line generic `FastMCP` wrapper: discovers tools, registers them, runs the chosen transport. Requires the `[server]` extra. |

## Quickstart

A server following this pattern looks like:

```
my-server/
  tools/
    __init__.py          # from .science import compute_thing; __all__ = ["compute_thing"]
    science.py            # plain Python, NO mcp imports
  mcp_server/
    __main__.py
  pyproject.toml          # [tool.mcp-server] tool_modules = ["tools"]
```

`tools/science.py`:

```python
from typing import Annotated
from pydantic import Field
from mcp_server_toolkit import ArtifactResult

def compute_thing(
    x: Annotated[float, Field(description="Input value")],
) -> ArtifactResult:
    """Compute a thing from x and return it as structured metadata."""
    return ArtifactResult.ok(message=f"computed {x ** 2}", value=x ** 2)
```

`pyproject.toml`:

```toml
[tool.mcp-server]
tool_modules = ["tools"]
```

`mcp_server/__main__.py`:

```python
from mcp_server_toolkit.cli import parse_server_args
from mcp_server_toolkit.server import run_server

if __name__ == "__main__":
    args = parse_server_args()
    run_server("my-server", transport=args.transport, host=args.host, port=args.port)
```

Run it:

```bash
python -m mcp_server --transport stdio
```

Because `tools/science.py` has no MCP imports, it's testable as plain
Python with no server running:

```python
from tools.science import compute_thing

def test_compute_thing():
    result = compute_thing(3.0)
    assert result.is_ok()
    assert result.metadata["value"] == 9.0
```

## Design principles (from the reference architecture)

1. `ArtifactResult` is the uniform return contract.
2. Arrays move between tools as file paths, never through agent context.
3. `__all__` in tool modules gates what becomes an MCP tool.
4. Type hints + `Annotated[..., Field(...)]` + docstrings generate the
   full tool schema — no separate schema file to maintain.
5. Tools are testable as plain Python; no server needs to be running.
6. `publish_outputs` handles the local-path → hosted-URL translation
   for cloud/tunnel deployments (`OUTPUT_ROOT` / `ARTIFACT_URL`).
7. `MCP_PUBLIC=1` disables DNS rebinding protection for tunnel serving.
8. Stale ports from suspended dev processes are auto-cleared.
9. Heavy scientific dependencies should be imported lazily, inside the
   function that needs them — not at module scope — so that
   `discover_tool_modules` and test collection stay fast and don't
   require every heavy dependency to be installed just to list tools.

## Status

Early, actively used internally to standardize new MCP servers across
Nesar's cosmology / particle-physics / ML tooling (BBN, sterile
neutrinos, dark-matter direct detection, weak lensing, hydro
emulators). Contributions and issues welcome.

## License

MIT — see [LICENSE](LICENSE).
