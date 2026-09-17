"""Тесты render_document() и round-trip через parse → render → parse."""
from __future__ import annotations

from pathlib import Path

from app.schemas.document import BlockType
from app.services.docx_parser import parse_docx
from app.services.renderer import render_document


def test_render_creates_file(
    simple_docx: Path, tmp_media_dir: Path, tmp_path: Path
) -> None:
    parsed = parse_docx(simple_docx, tmp_media_dir, project_id="test")
    out = tmp_path / "out.docx"

    result = render_document(parsed, out, title_page_marker_skip=False)

    assert Path(result).exists()
    assert Path(result).stat().st_size > 0


def test_render_preserves_paragraph_count(
    simple_docx: Path, tmp_media_dir: Path, tmp_path: Path
) -> None:
    parsed = parse_docx(simple_docx, tmp_media_dir, project_id="test")
    out = tmp_path / "out.docx"
    render_document(parsed, out, title_page_marker_skip=False)

    reparsed = parse_docx(out, tmp_media_dir, project_id="test")

    orig_paras = [b for b in parsed.blocks if b.type == BlockType.PARAGRAPH]
    new_paras = [b for b in reparsed.blocks if b.type == BlockType.PARAGRAPH]
    assert len(new_paras) == len(orig_paras)


def test_render_preserves_table(
    with_table_docx: Path, tmp_media_dir: Path, tmp_path: Path
) -> None:
    parsed = parse_docx(with_table_docx, tmp_media_dir, project_id="test")
    out = tmp_path / "out.docx"
    render_document(parsed, out, title_page_marker_skip=False)

    reparsed = parse_docx(out, tmp_media_dir, project_id="test")

    tables = [b for b in reparsed.blocks if b.type == BlockType.TABLE]
    assert len(tables) == 1
    assert tables[0].rows[0][0] == "Заголовок 1"
    assert tables[0].rows[2][2] == "f"


def test_render_preserves_table_position(
    with_table_docx: Path, tmp_media_dir: Path, tmp_path: Path
) -> None:
    """Таблица не должна уезжать в конец."""
    parsed = parse_docx(with_table_docx, tmp_media_dir, project_id="test")
    out = tmp_path / "out.docx"
    render_document(parsed, out, title_page_marker_skip=False)

    reparsed = parse_docx(out, tmp_media_dir, project_id="test")
    types = [b.type for b in reparsed.blocks]
    table_idx = types.index(BlockType.TABLE)

    assert any(t == BlockType.PARAGRAPH for t in types[:table_idx])
    assert any(t == BlockType.PARAGRAPH for t in types[table_idx + 1:])


def test_render_preserves_images(
    with_images_docx: Path, tmp_media_dir: Path, tmp_path: Path
) -> None:
    parsed = parse_docx(with_images_docx, tmp_media_dir, project_id="test")
    out = tmp_path / "out.docx"
    render_document(parsed, out, title_page_marker_skip=False)

    reparsed = parse_docx(out, tmp_media_dir, project_id="test")

    images = [b for b in reparsed.blocks if b.type == BlockType.IMAGE]
    assert len(images) == 2


def test_render_roundtrip_block_types_match(
    mixed_docx: Path, tmp_media_dir: Path, tmp_path: Path
) -> None:
    """После round-trip порядок типов блоков совпадает."""
    parsed1 = parse_docx(mixed_docx, tmp_media_dir, project_id="test")
    out = tmp_path / "out.docx"
    render_document(parsed1, out, title_page_marker_skip=False)

    parsed2 = parse_docx(out, tmp_media_dir, project_id="test")

    types1 = [b.type for b in parsed1.blocks]
    types2 = [b.type for b in parsed2.blocks]
    assert types1 == types2


def test_render_skips_preamble(
    with_sections_docx: Path, tmp_media_dir: Path, tmp_path: Path
) -> None:
    """С title_page_marker_skip=True блоки из preamble не рендерятся."""
    parsed = parse_docx(with_sections_docx, tmp_media_dir, project_id="test")
    out = tmp_path / "out.docx"
    render_document(parsed, out, title_page_marker_skip=True)

    reparsed = parse_docx(out, tmp_media_dir, project_id="test")

    sections_in_result = {b.section_id for b in reparsed.blocks}
    # preamble не должно быть
    assert "preamble" not in sections_in_result