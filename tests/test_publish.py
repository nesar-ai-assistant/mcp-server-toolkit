"""Tests for mcp_server_toolkit.publish.publish_outputs."""

from __future__ import annotations

import os

import pytest

from mcp_server_toolkit.artifact import ArtifactResult
from mcp_server_toolkit.publish import publish_outputs


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OUTPUT_ROOT", raising=False)
    monkeypatch.delenv("ARTIFACT_URL", raising=False)


def test_noop_when_env_not_set(tmp_path: os.PathLike[str]) -> None:
    @publish_outputs
    def tool() -> ArtifactResult:
        return ArtifactResult.ok(files=[str(tmp_path) + "/plot.png"])

    result = tool()
    assert result.files == [str(tmp_path) + "/plot.png"]


def test_rewrites_paths_under_output_root(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    local_file = output_dir / "plot.png"
    local_file.write_text("fake png")

    monkeypatch.setenv("OUTPUT_ROOT", str(output_dir))
    monkeypatch.setenv("ARTIFACT_URL", "https://example.com/artifacts")

    @publish_outputs
    def tool() -> ArtifactResult:
        return ArtifactResult.ok(files=[str(local_file)])

    result = tool()
    assert result.files == ["https://example.com/artifacts/plot.png"]


def test_leaves_paths_outside_output_root_untouched(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    outside_file = tmp_path / "elsewhere.png"

    monkeypatch.setenv("OUTPUT_ROOT", str(output_dir))
    monkeypatch.setenv("ARTIFACT_URL", "https://example.com/artifacts")

    @publish_outputs
    def tool() -> ArtifactResult:
        return ArtifactResult.ok(files=[str(outside_file)])

    result = tool()
    assert result.files == [str(outside_file)]


def test_works_on_plain_dict_results(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    local_file = output_dir / "data.npy"
    local_file.write_text("fake array")

    monkeypatch.setenv("OUTPUT_ROOT", str(output_dir))
    monkeypatch.setenv("ARTIFACT_URL", "https://example.com/artifacts")

    @publish_outputs
    def tool() -> dict:
        return {"status": "ok", "files": [str(local_file)]}

    result = tool()
    assert result["files"] == ["https://example.com/artifacts/data.npy"]
