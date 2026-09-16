"""Общие фикстуры для тестов doc-service."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Чтобы `import app` работал из tests/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests import helpers  # noqa: E402


@pytest.fixture
def tmp_docx_dir(tmp_path: Path) -> Path:
    """Папка для входных DOCX."""
    d = tmp_path / "docx"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def tmp_media_dir(tmp_path: Path) -> Path:
    """Папка для извлечённых картинок."""
    d = tmp_path / "media"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def simple_docx(tmp_docx_dir: Path) -> Path:
    return helpers.make_simple_docx(tmp_docx_dir / "simple.docx")


@pytest.fixture
def with_table_docx(tmp_docx_dir: Path) -> Path:
    return helpers.make_with_table_docx(tmp_docx_dir / "with_table.docx")


@pytest.fixture
def with_images_docx(tmp_docx_dir: Path) -> Path:
    return helpers.make_with_images_docx(tmp_docx_dir / "with_images.docx")


@pytest.fixture
def with_sections_docx(tmp_docx_dir: Path) -> Path:
    return helpers.make_with_sections_docx(tmp_docx_dir / "with_sections.docx")


@pytest.fixture
def mixed_docx(tmp_docx_dir: Path) -> Path:
    return helpers.make_mixed_docx(tmp_docx_dir / "mixed.docx")