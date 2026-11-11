from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


DraftBlockType = Literal["paragraph", "heading", "image", "table", "page_break"]


class DraftBlock(BaseModel):
    id: str = Field(..., min_length=1)
    type: DraftBlockType
    text: str | None = None
    image_id: str | None = None
    caption: str | None = None
    rows: list[list[str]] | None = None


class DraftSection(BaseModel):
    id: str = Field(..., min_length=1)
    title: str = ""
    blocks: list[DraftBlock] = Field(default_factory=list)


class DraftTitlePage(BaseModel):
    faculty: str = ""
    department: str = ""
    student_group: str = ""
    lab_title: str = ""
    lab_number: str = ""
    student_name: str = ""
    reviewer_name: str = ""
    discipline: str = ""


class DocumentDraft(BaseModel):
    schema_version: int = Field(default=1, ge=1)
    project_id: str = Field(..., min_length=1)
    source_type: Literal["blank", "docx"] = "blank"
    title_page: DraftTitlePage = Field(default_factory=DraftTitlePage)
    sections: list[DraftSection] = Field(default_factory=list)
    bibliography: list[str] = Field(default_factory=list)
    images: list[dict[str, Any]] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=lambda: {"gost_profile": "default"})
    version: int = Field(default=1, ge=1)


class ProjectCreateRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    title: str = ""


class ProjectCreateResponse(BaseModel):
    project_id: str
    user_id: str
    source_type: str
    status: str
    title: str


class ProjectDraftUpdateRequest(BaseModel):
    version: int = Field(..., ge=1)
    draft: DocumentDraft


class ProjectDraftResponse(BaseModel):
    project_id: str
    source_type: str
    version: int
    draft: DocumentDraft


class ProjectUploadResponse(BaseModel):
    project_id: str
    status: str
    source_filename: str


class ProjectStatusResponse(BaseModel):
    project_id: str
    user_id: str | None = None
    status: str
    source_type: str
    source_filename: str | None = None
    created_at: datetime
    updated_at: datetime


class ProjectDeleteResponse(BaseModel):
    project_id: str
    status: str


class ProjectAnalysisResponse(BaseModel):
    project_id: str
    status: str
    analysis: dict


class ProjectFileUploadResponse(BaseModel):
    project_id: str
    status: str
    file_path: str
    file_type: str


class ProjectProcessResponse(BaseModel):
    project_id: str
    task_id: str
    status: str
    report: dict


class ProjectSuggestionsResponse(BaseModel):
    project_id: str
    status: str
    suggestions: list[dict]


class ApplySuggestionsBody(BaseModel):
    suggestion_ids: list[str]


class ApplySuggestionsResponse(BaseModel):
    project_id: str
    status: str
    applied_ids: list[str]
