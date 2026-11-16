"""Hosted-deployment output rewriting for MCP tool functions.

When an MCP server is deployed behind a tunnel or on shared hosting,
tools that write local files (plots, data products) need those paths
translated into URLs a remote client can actually fetch. The
``publish_outputs`` decorator wraps a tool function, and if the
``OUTPUT_ROOT`` / ``ARTIFACT_URL`` environment variables are set,
rewrites any file path under ``OUTPUT_ROOT`` in the returned
:class:`~mcp_server_toolkit.artifact.ArtifactResult` (or any object
with a ``files: list[str]`` attribute) into a URL under
``ARTIFACT_URL``.

If neither environment variable is set (the common local/stdio case),
the decorator is a transparent no-op.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


def _rewrite_path(path: str, output_root: Path, artifact_url: str) -> str:
    """Rewrite a single file path if it falls under ``output_root``."""
    try:
        resolved = Path(path).resolve()
        relative = resolved.relative_to(output_root.resolve())
    except ValueError:
        # Not under OUTPUT_ROOT -- leave untouched.
        return path
    return f"{artifact_url.rstrip('/')}/{relative.as_posix()}"


def publish_outputs(func: Callable[..., T]) -> Callable[..., T]:
    """Rewrite local file paths in a tool's result to hosted URLs.

    Looks for ``OUTPUT_ROOT`` (local directory tool outputs are written
    under) and ``ARTIFACT_URL`` (public base URL that serves that same
    directory) in the environment. When both are set, any path in the
    result's ``files`` list that lives under ``OUTPUT_ROOT`` is rewritten
    to the corresponding ``ARTIFACT_URL`` path.

    Works with any return value that exposes a ``files: list[str]``
    attribute (e.g. :class:`~mcp_server_toolkit.artifact.ArtifactResult`)
    as well as bare dicts with a ``"files"`` key. All other return types
    pass through unchanged.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        result: Any = func(*args, **kwargs)

        output_root_env = os.environ.get("OUTPUT_ROOT")
        artifact_url = os.environ.get("ARTIFACT_URL")
        if not output_root_env or not artifact_url:
            return result  # type: ignore[no-any-return]

        output_root = Path(output_root_env)

        if hasattr(result, "files") and isinstance(result.files, list):
            new_files = [
                _rewrite_path(f, output_root, artifact_url) if isinstance(f, str) else f
                for f in result.files
            ]
            try:
                result.files = new_files
            except (AttributeError, TypeError):
                # Immutable model (e.g. frozen pydantic) -- rebuild via copy if possible.
                model_copy = getattr(result, "model_copy", None)
                if callable(model_copy):
                    result = model_copy(update={"files": new_files})
        elif isinstance(result, dict) and isinstance(result.get("files"), list):
            result = dict(result)
            result["files"] = [
                _rewrite_path(f, output_root, artifact_url) if isinstance(f, str) else f
                for f in result["files"]
            ]

        return result  # type: ignore[no-any-return]

    return wrapper
