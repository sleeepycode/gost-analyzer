from pathlib import Path

from docx import Document

from app.core.config import settings
from app.schemas.draft import DocumentDraft, DraftBlock, DraftSection
from app.services.draft_assembler import assemble_draft_document, build_legacy_document


def test_assemble_draft_creates_formatted_docx(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path / "storage"))
    monkeypatch.setattr(settings, "input_dir", str(tmp_path / "storage" / "inputs"))
    monkeypatch.setattr(settings, "output_dir", str(tmp_path / "storage" / "outputs"))
    monkeypatch.setattr(settings, "report_dir", str(tmp_path / "storage" / "reports"))

    draft = DocumentDraft(
        project_id="draft-project",
        title_page={
            "lab_title": "Тестовый отчёт",
            "department": "Кафедра ИС",
            "discipline": "Программирование",
            "lab_number": "1",
            "student_group": "БПИ-01",
            "student_name": "Иванов И.И.",
            "reviewer_name": "Петров П.П.",
        },
        sections=[
            DraftSection(
                id="introduction",
                title="Введение",
                blocks=[
                    DraftBlock(id="p1", type="paragraph", text="Текст введения."),
                    DraftBlock(id="t1", type="table", rows=[["A", "B"], ["1", "2"]]),
                ],
            )
        ],
        bibliography=["Источник 1"],
    )

    result = assemble_draft_document("draft-project", draft)
    output_path = Path(result["output_path"])

    assert result["status"] == "completed"
    assert output_path.exists()
    assert output_path.stat().st_size > 0

    document = Document(str(output_path))
    texts = [paragraph.text for paragraph in document.paragraphs]
    assert "Введение" in texts
    assert "Текст введения." in texts
    assert any("Тестовый отчёт" in text for text in texts)
    assert len(document.tables) == 1


def test_build_legacy_structure_creates_docx(tmp_path):
    output_path = tmp_path / "legacy.docx"
    build_legacy_document(
        {
            "content_blocks": [
                {"type": "paragraph", "data": {"text": "Старый абзац."}},
                {"type": "table", "data": {"rows": [["A", "B"]]}},
            ],
            "introduction": {"title": "Введение", "content": "Текст раздела."},
        },
        output_path,
    )

    assert output_path.exists()
    document = Document(str(output_path))
    assert any(paragraph.text == "Старый абзац." for paragraph in document.paragraphs)
    assert any(paragraph.text == "Введение" for paragraph in document.paragraphs)
    assert len(document.tables) == 1
