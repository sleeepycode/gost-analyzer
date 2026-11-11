from __future__ import annotations

from app.schemas.project import DocumentDraft, DraftSection
from app.services.storage import read_project_draft, write_project_draft


DEFAULT_SECTIONS = (
    ("introduction", "Введение"),
    ("theory", "Теоретическая часть"),
    ("practice", "Практическая часть"),
    ("conclusion", "Заключение"),
)


def build_default_draft(project_id: str, title: str = "") -> DocumentDraft:
    return DocumentDraft(
        project_id=project_id,
        source_type="blank",
        title_page={"lab_title": title.strip()},
        sections=[DraftSection(id=section_id, title=section_title) for section_id, section_title in DEFAULT_SECTIONS],
    )


def load_draft(project_id: str) -> DocumentDraft | None:
    raw = read_project_draft(project_id)
    if raw is None:
        return None
    return DocumentDraft.model_validate(raw)


def save_draft(draft: DocumentDraft) -> str:
    return write_project_draft(draft.project_id, draft.model_dump(mode="json"))
