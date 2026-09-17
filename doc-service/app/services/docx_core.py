import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path('storage') / 'projects'
PROJECT_ROOT.mkdir(parents=True, exist_ok=True)


def ensure_project_dir(project_id: str) -> Path:
    project_dir = PROJECT_ROOT / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')