"""
HTTP-клиент ML (POST /analyze).

Важно:
- Backend №1 передаёт пользовательские картинки в ML напрямую.
- Картинки передаются по HTTP URL, а не локальными путями Windows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings


def _base_url() -> str | None:
    base = (settings.ml_service_base_url or '').strip().rstrip('/')
    return base or None


def _backend_public_url() -> str:
    return (settings.backend_public_url or 'http://127.0.0.1:8002').strip().rstrip('/')


def is_configured() -> bool:
    return _base_url() is not None


def ping() -> dict:
    base = _base_url()
    if not base:
        return {'ok': False, 'error': 'ml_service_base_url не задан'}
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f'{base}/health')
        if response.is_success:
            return {'ok': True, 'status_code': response.status_code}
        return {'ok': False, 'status_code': response.status_code, 'error': response.text[:200]}
    except Exception as exc:
        return {'ok': False, 'error': str(exc)}


def image_file_to_public_url(image_path: Path) -> str:
    """
    storage/projects/{id}/images/a.png -> http://127.0.0.1:8002/storage/projects/{id}/images/a.png
    """
    path = Path(image_path)
    normalized = str(path).replace('\\', '/')
    marker = 'storage/'
    if marker in normalized:
        relative = normalized[normalized.index(marker):]
    else:
        relative = normalized.lstrip('/')
    return f'{_backend_public_url()}/{relative}'


def build_image_item(image_path: Path, source: str = 'user_uploaded_image') -> dict[str, Any]:
    return {
        'image_id': image_path.stem,
        'path': image_file_to_public_url(image_path),
        'source': source,
        'filename': image_path.name,
        'local_path': str(image_path),
    }


def analyze_images(
    image_paths: list[str],
    topic: str,
    document_text: str = '',
    project_id: str | None = None,
) -> dict:
    """POST /analyze по контракту ML: document_text + images[].path URL."""
    base = _base_url()
    if not base:
        raise RuntimeError('Не задан ml_service_base_url в .env')

    images = []
    for raw in image_paths:
        path = Path(raw)
        if path.exists():
            images.append(build_image_item(path))
        else:
            # fallback: если уже прислали URL или относительный путь
            images.append({
                'image_id': Path(str(raw)).stem or 'image',
                'path': str(raw),
                'source': 'user_uploaded_image',
                'filename': Path(str(raw)).name,
            })

    payload = {
        'project_id': project_id or '',
        'document_text': document_text or '',
        'image_paths': [],
        'image_urls': [],
        'images': images,
        'topic': topic or 'лабораторной работы',
    }

    with httpx.Client(timeout=float(getattr(settings, 'ml_timeout', 900))) as client:
        response = client.post(f'{base}/analyze', json=payload)
    if not response.is_success:
        detail = response.text[:500]
        raise RuntimeError(f'ML analyze: {response.status_code} {detail}')
    return response.json()


def analyze_image_file(
    image_path: Path,
    topic: str,
    document_text: str = '',
    project_id: str | None = None,
) -> dict:
    """Анализ одного пользовательского изображения."""
    result = analyze_images([str(image_path)], topic, document_text, project_id=project_id)
    images = result.get('images') or []
    if images:
        return images[0]
    errors = result.get('errors') or []
    if errors:
        raise RuntimeError(str(errors[0]))
    raise RuntimeError('ML не вернул данные по изображению')
