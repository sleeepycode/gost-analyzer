from __future__ import annotations
from ml.logger import logger


from typing import Any

from ml.service import analyze_project


def _analyze_project_payload_raw(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Adapter for backend requests.

    Supports two formats:
    1) old/simple:
       {"document_text": "...", "image_paths": ["..."]}

    2) URL-based:
       {"document_text": "...", "image_urls": ["http://backend/.../image.png"]}

    3) extended:
       {"document_text": "...", "images": [{"path": "...", "source": "back1_user_upload"}]}

    Field images[].path may contain either local path or HTTP/HTTPS URL.
    """
    document_text = payload.get("document_text", "") or ""
    topic = payload.get("topic", "лабораторной работы") or "лабораторной работы"

    image_paths = list(payload.get("image_paths") or [])
    image_paths.extend(payload.get("image_urls") or [])
    images_meta = payload.get("images") or []

    for item in images_meta:
        if isinstance(item, dict) and item.get("path"):
            image_paths.append(item["path"])

    # remove duplicates preserving order
    image_paths = list(dict.fromkeys(image_paths))

    result = analyze_project(
        document_text=document_text,
        image_paths=image_paths,
        topic=topic,
    )

    # Preserve project_id for backend traceability.
    if payload.get("project_id") is not None:
        result["project_id"] = payload.get("project_id")

    # Return source/image_id if backend sent extended images.
    meta_by_path = {
        item.get("path"): item
        for item in images_meta
        if isinstance(item, dict) and item.get("path")
    }

    for image in result.get("images", []):
        meta = meta_by_path.get(image.get("path"), {})
        if meta.get("image_id") is not None:
            image["image_id"] = meta.get("image_id")
        if meta.get("source") is not None:
            image["source"] = meta.get("source")

        target_section = (
            image.get("recommended_section")
            or image.get("placement", {}).get("section")
            or "practice"
        )

        image["insert"] = {
            "enabled": True,
            "mode": "image",
            "target_section": target_section,
            "caption": True,
            "caption_position": "below",
            "ocr_text_as_note": False,
            "width_cm": 12,
        }

    return result


def analyze_project_payload(payload: dict):
    logger.info("api_adapter.analyze_project_payload started")
    logger.info(f"payload_keys={list(payload.keys())}")
    logger.info(f"project_id={payload.get('project_id')}")
    logger.info(f"image_paths_count={len(payload.get('image_paths') or [])}")
    logger.info(f"image_urls_count={len(payload.get('image_urls') or [])}")
    logger.info(f"images_meta_count={len(payload.get('images') or [])}")

    try:
        result = _analyze_project_payload_raw(payload)
        logger.info("api_adapter.analyze_project_payload finished")
        return result
    except Exception as exc:
        logger.error(f"api_adapter.analyze_project_payload failed: {exc}")
        raise
