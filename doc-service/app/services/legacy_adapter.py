from __future__ import annotations

from typing import Any

from app.schemas.document import Block, BlockType, ParsedDocument


def to_legacy(parsed: ParsedDocument) -> dict[str, Any]:
    """
    Возвращает ровно тот формат, что отдавал старый /extract:
    { paragraphs: [...], tables: [...], images: [...], content_blocks: [...] }

    Backend и ML не должны заметить разницы.
    """
    paragraphs: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []
    content_blocks: list[dict[str, Any]] = []

    para_index = 0
    table_index = 0
    image_index = 0

    for block in parsed.blocks:
        if block.type == BlockType.HEADING or block.type == BlockType.PARAGRAPH:
            meta = {
                "id": f"paragraph_{para_index + 1}",
                "text": block.text or "",
                "source": "original_docx_paragraph",
                "type": "paragraph",
                "position": para_index,
            }
            paragraphs.append(meta)
            content_blocks.append({"type": "paragraph", "data": meta})
            para_index += 1

        elif block.type == BlockType.TABLE:
            meta = {
                "id": f"table_{table_index + 1}",
                "rows": block.rows or [],
                "source": "original_docx_table",
                "type": "table",
                "position": table_index,
            }
            tables.append(meta)
            content_blocks.append({"type": "table", "data": meta})
            table_index += 1

        elif block.type == BlockType.IMAGE:
            # legacy-формат использует insert_before_paragraph = индекс параграфа
            insert_before = _find_insert_position_for_image(block, parsed)
            meta = {
                "id": f"image_{image_index + 1}",
                "path": block.image_path or "",
                "source": "original_docx_image",
                "type": "image",
                "caption": block.caption,
                "position": image_index,
                "context_text": None,
                "insert_before_paragraph": insert_before,
            }
            images.append(meta)
            content_blocks.append({"type": "image", "data": meta})
            image_index += 1

    return {
        "paragraphs": paragraphs,
        "tables": tables,
        "images": images,
        "content_blocks": content_blocks,
    }


def _find_insert_position_for_image(block: Block, parsed: ParsedDocument) -> int:
    """
    Возвращает индекс параграфа, ДО которого идёт картинка.

    Логика: считаем все paragraph/heading-блоки, которые идут раньше картинки.
    Это ровно то, что старый extractor клал в insert_before_paragraph.
    """
    count = 0
    for b in parsed.blocks:
        if b.position >= block.position:
            break
        if b.type in (BlockType.HEADING, BlockType.PARAGRAPH):
            count += 1
    return count