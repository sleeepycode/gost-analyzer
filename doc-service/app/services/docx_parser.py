from __future__ import annotations

import logging
import zipfile
from pathlib import Path

from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.schemas.document import (
    Block,
    BlockType,
    ParsedDocument,
    Section,
)
from app.services.section_detector import (
    detect_section,
    is_heading,
    normalize_heading,
)

logger = logging.getLogger(__name__)

# Порядок, в котором идут «каноничные» разделы.
# Используется только для нумерации order в Section.
SECTION_ORDER_HINT = [
    "introduction",
    "theory",
    "practice",
    "conclusion",
    "bibliography",
]


# ----------------------------------------------------------------------
# Обход тела DOCX
# ----------------------------------------------------------------------

def iter_block_items(parent: DocxDocument):
    """Идём по телу документа в реальном порядке: p, t, p, t, ..."""
    body = parent.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def paragraph_contains_drawing(paragraph: Paragraph) -> bool:
    xml = paragraph._p.xml
    return "<w:drawing" in xml or "<pic:pic" in xml


def extract_media_files(docx_path: str | Path, media_dir: str | Path) -> dict[str, str]:
    """
    Распаковывает word/media/* из DOCX в media_dir.
    Возвращает mapping: media_file_name -> local path.
    """
    docx_path = Path(docx_path)
    media_dir = Path(media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)

    media: dict[str, str] = {}

    with zipfile.ZipFile(docx_path, "r") as archive:
        for name in archive.namelist():
            if not name.startswith("word/media/"):
                continue
            filename = Path(name).name
            target = media_dir / filename
            with archive.open(name) as src, target.open("wb") as dst:
                dst.write(src.read())
            media[filename] = str(target)

    logger.info("Extracted %d media files to %s", len(media), media_dir)
    return media


def extract_table_rows(table: Table) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.rows:
        rows.append([cell.text.strip() for cell in row.cells])
    return rows


# ----------------------------------------------------------------------
# Генерация ID
# ----------------------------------------------------------------------

class IdGenerator:
    """p_0001, h_0002, t_0003, img_0004 — стабильные и читаемые ID."""

    def __init__(self) -> None:
        self._counters = {"p": 0, "h": 0, "t": 0, "img": 0}

    def next(self, prefix: str) -> str:
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return f"{prefix}_{self._counters[prefix]:04d}"


# ----------------------------------------------------------------------
# Основной парсер
# ----------------------------------------------------------------------

def parse_docx(
    docx_path: str | Path,
    media_dir: str | Path,
    project_id: str,
) -> ParsedDocument:
    """
    Парсит DOCX в ParsedDocument.

    :param docx_path: путь к исходному DOCX
    :param media_dir: куда распаковать картинки
    :param project_id: ID проекта (для ParsedDocument)
    """
    docx_path = Path(docx_path)
    media_dir = Path(media_dir)

    if not docx_path.exists():
        raise FileNotFoundError(f"DOCX not found: {docx_path}")

    doc = Document(str(docx_path))
    media_files = extract_media_files(docx_path, media_dir)

    # Упорядоченный список имён картинок — соответствует порядку появления
    # в документе. python-docx не даёт прямого доступа к имени картинки
    # внутри параграфа, поэтому идём по media в порядке, который вернул zip.
    # Порядок media в DOCX = порядок вставки в большинстве редакторов,
    # но не гарантирован. Для точного сопоставления используем rels.
    media_order = _resolve_media_order(doc, media_files)

    ids = IdGenerator()
    blocks: list[Block] = []
    image_index = 0

    for item in iter_block_items(doc):
        if isinstance(item, Paragraph):
            text = item.text.strip()
            has_image = paragraph_contains_drawing(item)

            # Сначала картинка, потом текст этого же параграфа.
            if has_image and image_index < len(media_order):
                media_name = media_order[image_index]
                local_path = media_files.get(media_name, "")
                img_id = ids.next("img")
                blocks.append(
                    Block(
                        id=img_id,
                        type=BlockType.IMAGE,
                        position=len(blocks),
                        image_id=img_id,
                        image_path=local_path,
                        caption=None,
                    )
                )
                image_index += 1

            if text:
                heading = is_heading(text)
                if heading:
                    blocks.append(
                        Block(
                            id=ids.next("h"),
                            type=BlockType.HEADING,
                            position=len(blocks),
                            text=text,
                            level=1,
                        )
                    )
                else:
                    blocks.append(
                        Block(
                            id=ids.next("p"),
                            type=BlockType.PARAGRAPH,
                            position=len(blocks),
                            text=text,
                        )
                    )

        elif isinstance(item, Table):
            rows = extract_table_rows(item)
            blocks.append(
                Block(
                    id=ids.next("t"),
                    type=BlockType.TABLE,
                    position=len(blocks),
                    rows=rows,
                )
            )

    # Остались картинки, не привязанные к параграфам
    while image_index < len(media_order):
        media_name = media_order[image_index]
        local_path = media_files.get(media_name, "")
        img_id = ids.next("img")
        blocks.append(
            Block(
                id=img_id,
                type=BlockType.IMAGE,
                position=len(blocks),
                image_id=img_id,
                image_path=local_path,
                caption=None,
            )
        )
        image_index += 1

    sections = _build_sections(blocks)

    parsed = ParsedDocument(
        project_id=project_id,
        blocks=blocks,
        sections=sections,
        media={b.image_id: b.image_path for b in blocks
               if b.type == BlockType.IMAGE and b.image_id and b.image_path},
        metadata={
            "source_path": str(docx_path),
            "blocks_count": len(blocks),
            "sections_count": len(sections),
        },
    )

    logger.info(
        "Parsed DOCX: %d blocks, %d sections, %d images",
        len(parsed.blocks), len(parsed.sections), len(parsed.media),
    )
    return parsed


# ----------------------------------------------------------------------
# Привязка media к параграфам
# ----------------------------------------------------------------------

def _resolve_media_order(doc: DocxDocument, media_files: dict[str, str]) -> list[str]:
    """
    Возвращает имена media-файлов в порядке их появления в документе.

    Проходим по rels документа, отбираем image-rels, сортируем по rId.
    Это надёжнее, чем полагаться на порядок в zip.
    """
    result: list[str] = []
    seen: set[str] = set()

    for rel in doc.part.rels.values():
        if "image" not in rel.reltype:
            continue
        target = rel.target_ref  # "media/image1.png"
        name = Path(target).name
        if name in seen:
            continue
        if name in media_files:
            result.append(name)
            seen.add(name)

    # Если что-то из media не попало — добавим в конце
    for name in media_files:
        if name not in seen:
            result.append(name)
            seen.add(name)

    return result


# ----------------------------------------------------------------------
# Секции
# ----------------------------------------------------------------------

def _build_sections(blocks: list[Block]) -> list[Section]:
    """
    Разбивает блоки на секции по заголовкам.
    Блоки до первого заголовка образуют секцию 'preamble'.
    """
    sections: list[Section] = []
    current: Section | None = None
    order = 0
    current_heading_id: str | None = None

    for block in blocks:
        if block.type == BlockType.HEADING:
            section_id = detect_section(block.text or "") or f"section_{order + 1}"
            current = Section(
                id=section_id,
                title=normalize_heading(block.text or ""),
                heading_block_id=block.id,
                block_ids=[],
                order=order,
            )
            order += 1
            sections.append(current)
            block.section_id = section_id
            current_heading_id = block.id
            continue

        if current is None:
            # блоки до первого заголовка
            if not sections or sections[0].id != "preamble":
                current = Section(
                    id="preamble",
                    title="",
                    heading_block_id=None,
                    block_ids=[],
                    order=-1,
                )
                sections.insert(0, current)
            current.block_ids.append(block.id)
            block.section_id = "preamble"
            block.parent_heading_id = None
        else:
            current.block_ids.append(block.id)
            block.section_id = current.id
            block.parent_heading_id = current_heading_id

    # Присвоим order по порядку следования, кроме preamble
    for i, s in enumerate(sections):
        if s.id != "preamble":
            s.order = i

    return sections