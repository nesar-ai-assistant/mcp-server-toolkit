"""mcp-server-toolkit: shared scaffolding for science-MCP servers.

Extracted from the pattern converged on in ``HEP-KE/spectra-mcp-server``
(dispatch branch): the science code stays plain Python with no MCP
imports; a thin, generic wrapper publishes it as MCP tools.

Public API:

- :class:`mcp_server_toolkit.artifact.ArtifactResult` — uniform tool
  return contract (status, files, message, metadata).
- :func:`mcp_server_toolkit.publish.publish_outputs` — decorator that
  rewrites local output paths to a hosted ``ARTIFACT_URL`` root when
  ``OUTPUT_ROOT`` is configured (for tunnel/cloud deployments).
- :func:`mcp_server_toolkit.discovery.discover_tool_modules` — reads
  ``[tool.mcp-server].tool_modules`` from a ``pyproject.toml`` and
  imports the listed modules, collecting their ``__all__`` callables.
- :func:`mcp_server_toolkit.cli.build_arg_parser` — standard
  ``--transport {stdio,streamable-http} --host --port`` CLI parser
  shared by every server's ``mcp_server/cli.py``.
"""

from mcp_server_toolkit.artifact import ArtifactResult
from mcp_server_toolkit.cli import ServerArgs, build_arg_parser, parse_server_args
from mcp_server_toolkit.discovery import discover_tool_modules
from mcp_server_toolkit.publish import publish_outputs

__all__ = [
    "ArtifactResult",
    "ServerArgs",
    "build_arg_parser",
    "discover_tool_modules",
    "parse_server_args",
    "publish_outputs",
]

__version__ = "0.1.0"
