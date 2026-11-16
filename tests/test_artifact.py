"""Tests for mcp_server_toolkit.artifact.ArtifactResult."""

from __future__ import annotations

from mcp_server_toolkit.artifact import ArtifactResult


def test_default_status_is_ok() -> None:
    result = ArtifactResult()
    assert result.status == "ok"
    assert result.is_ok()
    assert result.files == []
    assert result.metadata == {}


def test_ok_constructor_sets_metadata_from_kwargs() -> None:
    result = ArtifactResult.ok("computed", files=["out.npy"], value=42)
    assert result.is_ok()
    assert result.message == "computed"
    assert result.files == ["out.npy"]
    assert result.metadata == {"value": 42}


def test_error_constructor() -> None:
    result = ArtifactResult.error("something broke", code=500)
    assert result.status == "error"
    assert not result.is_ok()
    assert result.files == []
    assert result.metadata == {"code": 500}


def test_partial_constructor() -> None:
    result = ArtifactResult.partial("half done", files=["a.png"], completed=3, total=10)
    assert result.status == "partial"
    assert not result.is_ok()
    assert result.files == ["a.png"]
    assert result.metadata == {"completed": 3, "total": 10}


def test_round_trips_through_json() -> None:
    result = ArtifactResult.ok("ok", files=["x.csv"], a=1, b="two")
    restored = ArtifactResult.model_validate_json(result.model_dump_json())
    assert restored == result
