"""Uniform return contract for MCP science tools.

Every tool function in the spectra-mcp-server pattern returns an
:class:`ArtifactResult` instead of raw arrays or ad-hoc dicts. This
keeps the MCP schema predictable for client agents and keeps large
numeric payloads (arrays, grids, FITS files) out of the agent's
context window -- they travel as file paths in ``files`` instead.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Status = Literal["ok", "error", "partial"]


class ArtifactResult(BaseModel):
    """Standard result object returned by every MCP tool function.

    Attributes:
        status: One of ``"ok"``, ``"error"``, or ``"partial"``.
        files: Absolute or ``OUTPUT_ROOT``-relative paths to any files
            produced by the tool (plots, arrays, tables). Arrays should
            move between tools as file paths, never inline through the
            agent context.
        message: Short, human-readable summary of what happened. Should
            be informative enough for an agent to decide the next step
            without opening any of ``files``.
        metadata: Free-form JSON-serializable dict for structured
            outputs (scalar results, parameter echoes, provenance).
    """

    status: Status = "ok"
    files: list[str] = Field(default_factory=list)
    message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_ok(self) -> bool:
        """Return True if ``status`` is ``"ok"``."""
        return self.status == "ok"

    @classmethod
    def ok(
        cls,
        message: str = "",
        files: list[str] | None = None,
        **metadata: Any,
    ) -> ArtifactResult:
        """Convenience constructor for a successful result."""
        return cls(status="ok", files=files or [], message=message, metadata=metadata)

    @classmethod
    def error(cls, message: str, **metadata: Any) -> ArtifactResult:
        """Convenience constructor for a failed result.

        Prefer this over raising inside a tool function: MCP clients
        get a structured, schema-valid response they can branch on
        instead of a stack trace serialized as text.
        """
        return cls(status="error", files=[], message=message, metadata=metadata)

    @classmethod
    def partial(
        cls,
        message: str,
        files: list[str] | None = None,
        **metadata: Any,
    ) -> ArtifactResult:
        """Convenience constructor for a partially-successful result."""
        return cls(status="partial", files=files or [], message=message, metadata=metadata)
