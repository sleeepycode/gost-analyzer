from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    IMAGE = "image"


# Для обратной совместимости с to_legacy()
LEGACY_TYPE_MAP = {
    BlockType.HEADING: "paragraph",
    BlockType.PARAGRAPH: "paragraph",
    BlockType.TABLE: "table",
    BlockType.IMAGE: "image",
}


@dataclass
class Block:
    """Атомарный элемент документа в порядке следования."""
    id: str
    type: BlockType
    position: int
    source: str = "original_docx"

    # Только один из этих наборов заполнен — по типу
    text: str | None = None
    level: int | None = None          # для heading
    rows: list[list[str]] | None = None  # для table
    image_id: str | None = None       # для image
    image_path: str | None = None     # локальный путь
    caption: str | None = None

    # Метаданные
    section_id: str | None = None
    parent_heading_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "id": self.id,
            "type": self.type.value,
            "position": self.position,
            "source": self.source,
            "section_id": self.section_id,
            "parent_heading_id": self.parent_heading_id,
        }
        if self.text is not None:
            data["text"] = self.text
        if self.level is not None:
            data["level"] = self.level
        if self.rows is not None:
            data["rows"] = self.rows
        if self.image_id is not None:
            data["image_id"] = self.image_id
        if self.image_path is not None:
            data["image_path"] = self.image_path
        if self.caption is not None:
            data["caption"] = self.caption
        return data


@dataclass
class Section:
    """Раздел документа: заголовок + блоки под ним."""
    id: str                            # "introduction", "theory", "custom_1", ...
    title: str
    heading_block_id: str | None       # ID блока-заголовка
    block_ids: list[str] = field(default_factory=list)
    order: int = 0


@dataclass
class ParsedDocument:
    project_id: str
    blocks: list[Block] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)
    media: dict[str, str] = field(default_factory=dict)  # image_id -> path
    metadata: dict[str, Any] = field(default_factory=dict)

    # --- Утилиты ---

    def get_block(self, block_id: str) -> Block | None:
        for b in self.blocks:
            if b.id == block_id:
                return b
        return None

    def get_section(self, section_id: str) -> Section | None:
        for s in self.sections:
            if s.id == section_id:
                return s
        return None

    def get_blocks_in_section(self, section_id: str) -> list[Block]:
        section = self.get_section(section_id)
        if not section:
            return []
        return [b for b in self.blocks if b.id in section.block_ids]

    def find_last_block_in_section(self, section_id: str) -> Block | None:
        blocks = self.get_blocks_in_section(section_id)
        return blocks[-1] if blocks else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "blocks": [b.to_dict() for b in self.blocks],
            "sections": [
                {
                    "id": s.id,
                    "title": s.title,
                    "heading_block_id": s.heading_block_id,
                    "block_ids": s.block_ids,
                    "order": s.order,
                }
                for s in self.sections
            ],
            "media": dict(self.media),
            "metadata": dict(self.metadata),
        }