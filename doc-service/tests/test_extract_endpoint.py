"""Тесты /documents/extract — проверка обратной совместимости."""
from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch) -> TestClient:
    """TestClient с изолированным storage."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "storage_dir", str(tmp_path / "storage"))
    monkeypatch.setattr(settings, "input_dir", str(tmp_path / "storage" / "inputs"))
    monkeypatch.setattr(settings, "output_dir", str(tmp_path / "storage" / "outputs"))
    monkeypatch.setattr(settings, "report_dir", str(tmp_path / "storage" / "reports"))

    # ensure_dirs создаст папки
    from app.core.config import ensure_dirs

    ensure_dirs()

    from app.main import create_app

    app = create_app()
    return TestClient(app)


def _docx_bytes(path: Path) -> bytes:
    return path.read_bytes()


def test_extract_returns_legacy_format(client: TestClient, with_table_docx: Path) -> None:
    files = {
        "file": (
            "with_table.docx",
            _docx_bytes(with_table_docx),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    response = client.post("/documents/extract", files=files)

    assert response.status_code == 200
    body = response.json()

    assert "project_id" in body
    assert "paragraphs" in body
    assert "tables" in body
    assert "images" in body

    assert len(body["tables"]) == 1
    assert body["tables"][0]["id"] == "table_1"
    assert body["tables"][0]["rows"][0][0] == "Заголовок 1"


def test_extract_saves_parsed_json(client: TestClient, with_table_docx: Path) -> None:
    files = {
        "file": (
            "with_table.docx",
            _docx_bytes(with_table_docx),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    response = client.post("/documents/extract", files=files)
    assert response.status_code == 200

    project_id = response.json()["project_id"]

    from app.core.config import settings

    project_dir = Path(settings.storage_dir) / "projects" / project_id

    assert (project_dir / "parsed.json").exists()
    assert (project_dir / "extract_response.json").exists()


def test_extract_rejects_non_docx(client: TestClient) -> None:
    files = {"file": ("notes.txt", b"text", "text/plain")}
    response = client.post("/documents/extract", files=files)

    assert response.status_code == 400


def test_extract_respects_provided_project_id(
    client: TestClient, simple_docx: Path
) -> None:
    files = {
        "file": (
            "simple.docx",
            _docx_bytes(simple_docx),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    response = client.post(
        "/documents/extract",
        files=files,
        data={"project_id": "my-project-123"},
    )

    assert response.status_code == 200
    assert response.json()["project_id"] == "my-project-123"


def test_extract_generates_project_id_when_missing(
    client: TestClient, simple_docx: Path
) -> None:
    files = {
        "file": (
            "simple.docx",
            _docx_bytes(simple_docx),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    response = client.post("/documents/extract", files=files)
    assert response.status_code == 200
    project_id = response.json()["project_id"]

    assert project_id
    assert len(project_id) == 32  # uuid4().hex


def test_extract_images_have_paths(
    client: TestClient, with_images_docx: Path
) -> None:
    files = {
        "file": (
            "with_images.docx",
            _docx_bytes(with_images_docx),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    response = client.post("/documents/extract", files=files)
    assert response.status_code == 200

    images = response.json()["images"]
    assert len(images) == 2
    for img in images:
        assert img["path"]
        assert Path(img["path"]).exists()