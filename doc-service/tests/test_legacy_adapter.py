"""Тесты legacy_adapter.to_legacy()."""
from __future__ import annotations

from pathlib import Path

from app.services.docx_parser import parse_docx
from app.services.legacy_adapter import to_legacy


def test_legacy_has_all_keys(with_table_docx: Path, tmp_media_dir: Path) -> None:
    parsed = parse_docx(with_table_docx, tmp_media_dir, project_id="test")
    legacy = to_legacy(parsed)

    assert set(legacy.keys()) == {"paragraphs", "tables", "images", "content_blocks"}


def test_legacy_paragraphs_format(with_table_docx: Path, tmp_media_dir: Path) -> None:
    parsed = parse_docx(with_table_docx, tmp_media_dir, project_id="test")
    legacy = to_legacy(parsed)

    assert len(legacy["paragraphs"]) > 0
    for p in legacy["paragraphs"]:
        assert "id" in p
        assert "text" in p
        assert "source" in p
        assert "type" in p
        assert "position" in p

        assert p["id"].startswith("paragraph_")
        assert p["source"] == "original_docx_paragraph"
        assert p["type"] == "paragraph"


def test_legacy_tables_format(with_table_docx: Path, tmp_media_dir: Path) -> None:
    parsed = parse_docx(with_table_docx, tmp_media_dir, project_id="test")
    legacy = to_legacy(parsed)

    assert len(legacy["tables"]) == 1
    table = legacy["tables"][0]

    assert table["id"] == "table_1"
    assert table["source"] == "original_docx_table"
    assert table["type"] == "table"
    assert len(table["rows"]) == 3
    assert table["rows"][0][0] == "Заголовок 1"


def test_legacy_images_format(with_images_docx: Path, tmp_media_dir: Path) -> None:
    parsed = parse_docx(with_images_docx, tmp_media_dir, project_id="test")
    legacy = to_legacy(parsed)

    assert len(legacy["images"]) == 2
    for img in legacy["images"]:
        assert img["id"].startswith("image_")
        assert img["source"] == "original_docx_image"
        assert img["type"] == "image"
        assert "path" in img
        assert "insert_before_paragraph" in img


def test_legacy_image_insert_positions(with_images_docx: Path, tmp_media_dir: Path) -> None:
    """insert_before_paragraph должен быть валидным индексом параграфа."""
    parsed = parse_docx(with_images_docx, tmp_media_dir, project_id="test")
    legacy = to_legacy(parsed)

    para_count = len(legacy["paragraphs"])

    for img in legacy["images"]:
        pos = img["insert_before_paragraph"]
        assert isinstance(pos, int)
        assert 0 <= pos <= para_count


def test_legacy_content_blocks_matches_lists(
    with_table_docx: Path, tmp_media_dir: Path
) -> None:
    """content_blocks должен содержать всё, что в paragraphs/tables/images."""
    parsed = parse_docx(with_table_docx, tmp_media_dir, project_id="test")
    legacy = to_legacy(parsed)

    content_types = [c["type"] for c in legacy["content_blocks"]]
    assert content_types.count("paragraph") == len(legacy["paragraphs"])
    assert content_types.count("table") == len(legacy["tables"])
    assert content_types.count("image") == len(legacy["images"])


def test_legacy_empty_document(tmp_docx_dir: Path, tmp_media_dir: Path) -> None:
    from docx import Document

    doc = Document()
    path = tmp_docx_dir / "empty.docx"
    doc.save(str(path))

    parsed = parse_docx(path, tmp_media_dir, project_id="test")
    legacy = to_legacy(parsed)

    assert legacy["paragraphs"] == []
    assert legacy["tables"] == []
    assert legacy["images"] == []