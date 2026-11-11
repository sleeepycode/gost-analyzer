from __future__ import annotations

import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

from app.core.config import settings
from app.schemas.draft import DocumentDraft, DraftBlock
from app.services.docx_core import ensure_project_dir
from app.services.gost_applier import apply_gost_formatting
from app.services.styles import (
    add_bibliography_item,
    add_gost_paragraph,
    add_heading_center,
    setup_document_styles,
)
from app.services.title_page_generator import generate_title_page

logger = logging.getLogger(__name__)


def _download_image(url: str) -> tuple[Path | None, str | None]:
    try:
        response = requests.get(url, timeout=(5, 30), headers={"User-Agent": "DocService/1.0"})
        response.raise_for_status()
        suffix = ".png"
        content_type = (response.headers.get("content-type") or "").lower()
        if "jpeg" in content_type or "jpg" in content_type:
            suffix = ".jpg"
        elif "webp" in content_type:
            suffix = ".webp"

        temporary = NamedTemporaryFile(delete=False, suffix=suffix, prefix="doc_service_draft_image_")
        with temporary:
            temporary.write(response.content)
        return Path(temporary.name), temporary.name
    except Exception as exc:
        logger.warning("Unable to download draft image %s: %s", url, exc)
        return None, None


def _resolve_image(image: dict) -> tuple[Path | None, str | None]:
    raw_path = str(image.get("path") or image.get("url") or image.get("local_path") or "")
    if not raw_path:
        return None, None
    if raw_path.startswith(("http://", "https://")):
        return _download_image(raw_path)

    path = Path(raw_path.replace("\\", "/"))
    if path.exists():
        return path, None
    logger.warning("Draft image file not found: %s", path)
    return None, None


def _add_table(doc: Document, rows: list[list[str]] | None) -> None:
    normalized_rows = rows or [[""]]
    columns = max((len(row) for row in normalized_rows), default=1)
    table = doc.add_table(rows=len(normalized_rows), cols=columns)
    table.style = "Table Grid"
    for row_index, row in enumerate(normalized_rows):
        for column_index in range(columns):
            table.cell(row_index, column_index).text = row[column_index] if column_index < len(row) else ""


def _add_image(doc: Document, block: DraftBlock, images_by_id: dict[str, dict], image_number: int, temp_files: list[str]) -> None:
    image = dict(images_by_id.get(block.image_id or "", {}))
    if block.caption:
        image["caption"] = block.caption
    path, temporary_path = _resolve_image(image)
    if temporary_path:
        temp_files.append(temporary_path)
    if not path:
        return

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(path), width=Cm(12))

    caption = block.caption or image.get("caption") or f"Рисунок {image_number}"
    caption_paragraph = doc.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph.add_run(str(caption))


def _render_block(
    doc: Document,
    block: DraftBlock,
    images_by_id: dict[str, dict],
    image_number: int,
    temp_files: list[str],
) -> int:
    if block.type == "paragraph":
        add_gost_paragraph(doc, block.text or "")
    elif block.type == "heading":
        add_heading_center(doc, block.text or "")
    elif block.type == "table":
        _add_table(doc, block.rows)
    elif block.type == "page_break":
        doc.add_page_break()
    elif block.type == "image":
        _add_image(doc, block, images_by_id, image_number, temp_files)
        image_number += 1
    return image_number


def _build_draft_body(draft: DocumentDraft, output_path: Path) -> None:
    doc = Document()
    setup_document_styles(doc)
    images_by_id = {
        str(item.get("image_id") or item.get("id")): item
        for item in draft.images
        if item.get("image_id") or item.get("id")
    }
    temp_files: list[str] = []
    image_number = 1

    try:
        for section in draft.sections:
            if section.title.strip():
                add_heading_center(doc, section.title.strip())
            for block in section.blocks:
                image_number = _render_block(doc, block, images_by_id, image_number, temp_files)

        if draft.bibliography:
            add_heading_center(doc, "Список использованных источников")
            for number, reference in enumerate(draft.bibliography, start=1):
                add_bibliography_item(doc, number, reference)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_path))
    finally:
        for temporary_path in temp_files:
            Path(temporary_path).unlink(missing_ok=True)


def _apply_title_page(input_path: Path, output_path: Path, draft: DocumentDraft) -> None:
    title_page = draft.title_page
    generate_title_page(
        input_path=str(input_path),
        output_path=str(output_path),
        department=title_page.department,
        discipline=title_page.discipline,
        lab_number=title_page.lab_number,
        lab_title=title_page.lab_title,
        student_group=title_page.student_group,
        student_name=title_page.student_name,
        reviewer_name=title_page.reviewer_name,
    )


def assemble_draft_document(project_id: str, draft: DocumentDraft) -> dict[str, str]:
    if draft.project_id != project_id:
        raise ValueError("project_id черновика не совпадает с project_id запроса")

    project_dir = ensure_project_dir(project_id)
    body_path = project_dir / f"{project_id}_draft_body.docx"
    gost_path = project_dir / f"{project_id}_draft_gost.docx"
    final_path = project_dir / f"{project_id}_final.docx"

    try:
        _build_draft_body(draft, body_path)
        apply_gost_formatting(str(body_path), str(gost_path))
        _apply_title_page(gost_path, final_path, draft)
    finally:
        body_path.unlink(missing_ok=True)
        gost_path.unlink(missing_ok=True)

    return {"status": "completed", "project_id": project_id, "output_path": str(final_path)}


def build_legacy_document(structure: dict, output_path: str | Path) -> None:
    """Собрать старую merged_structure без падения на отсутствующей функции."""
    doc = Document()
    setup_document_styles(doc)
    images = {
        str(item.get("id") or item.get("image_id")): item
        for item in structure.get("images") or []
        if item.get("id") or item.get("image_id")
    }
    rendered_image_ids: set[str] = set()
    temporary_files: list[str] = []
    image_number = 1

    try:
        for item in structure.get("content_blocks") or []:
            data = item.get("data") if isinstance(item, dict) else None
            block_type = item.get("type") if isinstance(item, dict) else None
            data = data or {}
            if block_type == "paragraph":
                add_gost_paragraph(doc, str(data.get("text") or ""))
            elif block_type == "table":
                _add_table(doc, data.get("rows"))
            elif block_type == "image":
                image_id = str(data.get("id") or data.get("image_id") or "")
                image_block = DraftBlock(
                    id=image_id or f"legacy-image-{image_number}",
                    type="image",
                    image_id=image_id or None,
                    caption=data.get("caption"),
                )
                image_number = _render_block(doc, image_block, images, image_number, temporary_files)
                if image_id:
                    rendered_image_ids.add(image_id)

        for image_id, image in images.items():
            if image_id in rendered_image_ids:
                continue
            image_block = DraftBlock(
                id=image_id or f"legacy-image-{image_number}",
                type="image",
                image_id=image_id or None,
                caption=image.get("caption"),
            )
            image_number = _render_block(doc, image_block, images, image_number, temporary_files)

        for section_key in ("introduction", "theory", "practice", "conclusion"):
            section = structure.get(section_key)
            if not isinstance(section, dict):
                continue
            add_heading_center(doc, str(section.get("title") or section_key))
            for paragraph in str(section.get("content") or "").splitlines():
                add_gost_paragraph(doc, paragraph)

        bibliography = structure.get("bibliography") or []
        if bibliography:
            add_heading_center(doc, "Список использованных источников")
            for number, reference in enumerate(bibliography, start=1):
                add_bibliography_item(doc, number, str(reference))

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output))
    finally:
        for temporary_path in temporary_files:
            Path(temporary_path).unlink(missing_ok=True)
