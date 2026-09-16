"""Тесты parse_docx."""
from __future__ import annotations

from pathlib import Path

from app.schemas.document import BlockType, ParsedDocument
from app.services.docx_parser import parse_docx


def test_parse_returns_parsed_document(simple_docx: Path, tmp_media_dir: Path) -> None:
    parsed = parse_docx(simple_docx, tmp_media_dir, project_id="test")

    assert isinstance(parsed, ParsedDocument)
    assert parsed.project_id == "test"
    assert len(parsed.blocks) >= 3


def test_parse_simple_paragraphs(simple_docx: Path, tmp_media_dir: Path) -> None:
    parsed = parse_docx(simple_docx, tmp_media_dir, project_id="test")

    paragraphs = [b for b in parsed.blocks if b.type == BlockType.PARAGRAPH]
    assert len(paragraphs) == 3
    assert "первый параграф" in (paragraphs[0].text or "").lower()
    assert "третий параграф" in (paragraphs[2].text or "").lower()


def test_parse_table_found(with_table_docx: Path, tmp_media_dir: Path) -> None:
    parsed = parse_docx(with_table_docx, tmp_media_dir, project_id="test")

    tables = [b for b in parsed.blocks if b.type == BlockType.TABLE]
    assert len(tables) == 1

    table = tables[0]
    assert table.rows is not None
    assert len(table.rows) == 3
    assert len(table.rows[0]) == 3
    assert table.rows[0][0] == "Заголовок 1"
    assert table.rows[2][2] == "f"


def test_parse_table_position_in_flow(with_table_docx: Path, tmp_media_dir: Path) -> None:
    """Таблица должна идти между параграфами, а не в конце."""
    parsed = parse_docx(with_table_docx, tmp_media_dir, project_id="test")

    types = [b.type for b in parsed.blocks]
    table_idx = types.index(BlockType.TABLE)

    # До таблицы — параграфы, после — тоже
    assert any(t == BlockType.PARAGRAPH for t in types[:table_idx])
    assert any(t == BlockType.PARAGRAPH for t in types[table_idx + 1:])


def test_parse_images_extracted(with_images_docx: Path, tmp_media_dir: Path) -> None:
    parsed = parse_docx(with_images_docx, tmp_media_dir, project_id="test")

    images = [b for b in parsed.blocks if b.type == BlockType.IMAGE]
    assert len(images) == 2

    for img in images:
        assert img.image_path is not None
        assert Path(img.image_path).exists()


def test_parse_images_order_preserved(with_images_docx: Path, tmp_media_dir: Path) -> None:
    parsed = parse_docx(with_images_docx, tmp_media_dir, project_id="test")

    images = [b for b in parsed.blocks if b.type == BlockType.IMAGE]
    assert images[0].position < images[1].position
    assert images[0].image_id != images[1].image_id


def test_parse_sections_built(with_sections_docx: Path, tmp_media_dir: Path) -> None:
    parsed = parse_docx(with_sections_docx, tmp_media_dir, project_id="test")

    section_ids = {s.id for s in parsed.sections}
    assert "introduction" in section_ids
    assert "theory" in section_ids
    assert "practice" in section_ids
    assert "conclusion" in section_ids


def test_parse_section_block_ids_link_to_blocks(
    with_sections_docx: Path, tmp_media_dir: Path
) -> None:
    parsed = parse_docx(with_sections_docx, tmp_media_dir, project_id="test")

    all_block_ids = {b.id for b in parsed.blocks}

    for section in parsed.sections:
        for bid in section.block_ids:
            assert bid in all_block_ids, f"section {section.id} refers to unknown block {bid}"


def test_parse_blocks_have_section_id_assigned(
    with_sections_docx: Path, tmp_media_dir: Path
) -> None:
    parsed = parse_docx(with_sections_docx, tmp_media_dir, project_id="test")

    for block in parsed.blocks:
        assert block.section_id is not None, f"block {block.id} has no section_id"


def test_parse_ids_are_stable_across_calls(
    simple_docx: Path, tmp_media_dir: Path
) -> None:
    parsed1 = parse_docx(simple_docx, tmp_media_dir, project_id="test")
    parsed2 = parse_docx(simple_docx, tmp_media_dir, project_id="test")

    ids1 = [b.id for b in parsed1.blocks]
    ids2 = [b.id for b in parsed2.blocks]
    assert ids1 == ids2


def test_parse_ids_are_unique(simple_docx: Path, tmp_media_dir: Path) -> None:
    parsed = parse_docx(simple_docx, tmp_media_dir, project_id="test")

    ids = [b.id for b in parsed.blocks]
    assert len(ids) == len(set(ids)), "IDs must be unique"


def test_parse_mixed_document(mixed_docx: Path, tmp_media_dir: Path) -> None:
    """Таблица, картинка и заголовки — все типы блоков присутствуют."""
    parsed = parse_docx(mixed_docx, tmp_media_dir, project_id="test")

    types = {b.type for b in parsed.blocks}
    assert BlockType.HEADING in types
    assert BlockType.PARAGRAPH in types
    assert BlockType.TABLE in types
    assert BlockType.IMAGE in types


def test_parse_media_mapping(mixed_docx: Path, tmp_media_dir: Path) -> None:
    """parsed.media содержит image_id -> path для всех картинок."""
    parsed = parse_docx(mixed_docx, tmp_media_dir, project_id="test")

    images = [b for b in parsed.blocks if b.type == BlockType.IMAGE]
    for img in images:
        assert img.image_id in parsed.media
        assert parsed.media[img.image_id] == img.image_path


def test_parse_to_dict_is_json_serializable(
    with_table_docx: Path, tmp_media_dir: Path
) -> None:
    """to_dict() должен давать JSON-совместимый результат."""
    import json

    parsed = parse_docx(with_table_docx, tmp_media_dir, project_id="test")
    data = parsed.to_dict()

    # Если упадёт — значит где-то остался несериализуемый объект
    json.dumps(data, ensure_ascii=False)


def test_parse_empty_document_fails(tmp_docx_dir: Path, tmp_media_dir: Path) -> None:
    """Несуществующий файл должен кинуть FileNotFoundError."""
    import pytest

    with pytest.raises(FileNotFoundError):
        parse_docx(tmp_docx_dir / "nonexistent.docx", tmp_media_dir, project_id="test")