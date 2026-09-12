import os
from ml.logger import logger

from ml.ai_report import analyze_report_structure
from ml.content_suggestions import build_content_suggestions
from ml.image_analyzer import analyze_image
from ml.numbering_generator import apply_numbering
from ml.schemas import build_project_response


def _build_fast_image_item(image_path: str, index: int) -> dict:
    return {
        "image_id": f"image_{index}",
        "path": image_path,
        "type": "image",
        "ocr_text": "",
        "caption": f"Рисунок {index} — Иллюстрация к отчёту",
        "recommended_section": "practice",
        "insert": {
            "enabled": True,
            "mode": "image",
            "target_section": "practice",
            "caption": True,
            "ocr_text_as_note": False,
        },
        "source": "fast_mode_no_ocr",
    }


def _analyze_project_raw(
    document_text: str,
    image_paths: list[str],
    topic: str = "лабораторной работы"
) -> dict:
    errors = []
    ai_used_total = False

    document_text = document_text or ""
    image_paths = image_paths or []
    topic = topic or "лабораторной работы"

    if not document_text.strip():
        errors.append("document_text is empty")

    structure, used = analyze_report_structure(document_text)
    ai_used_total = ai_used_total or used

    generated, bibliography, suggestions, used = build_content_suggestions(
        structure,
        topic,
        document_text
    )
    ai_used_total = ai_used_total or used

    report = {
        "found_sections": structure["found_sections"],
        "missing_sections": structure["missing_sections"],
        "has_required_structure": structure["has_required_structure"],
        "generated_sections": generated,
        "bibliography": bibliography
    }

    images = []

    image_analysis_mode = os.getenv("IMAGE_ANALYSIS_MODE", "fast").strip().lower()
    max_ocr_images = int(os.getenv("MAX_OCR_IMAGES", "0"))

    if image_analysis_mode == "fast" or max_ocr_images == 0:
        logger.info("Fast image mode enabled: skipping OCR/AI for images, returning insert instructions")
        for index, image_path in enumerate(image_paths, start=1):
            images.append(_build_fast_image_item(image_path, index))
    else:
        for index, image_path in enumerate(image_paths, start=1):
            if index > max_ocr_images:
                images.append(_build_fast_image_item(image_path, index))
                continue

            item, used = analyze_image(
                image_path,
                document_text,
                topic
            )

            ai_used_total = ai_used_total or used

            if item.get("error"):
                errors.append(f"{image_path}: {item['error']}")

            images.append(item)

    images = apply_numbering(images)

    return build_project_response(
        topic,
        report,
        images,
        suggestions,
        errors,
        ai_used_total
    )


def analyze_project(
    document_text: str,
    image_paths=None,
    topic: str = "лабораторная работа",
    *args,
    **kwargs
):
    image_paths = image_paths or []

    logger.info("ML analyze_project started")
    logger.info(f"document_text_len={len(document_text or '')}")
    logger.info(f"image_paths_count={len(image_paths)}")
    logger.info(f"topic={topic}")

    try:
        result = _analyze_project_raw(
            document_text=document_text,
            image_paths=image_paths,
            topic=topic
        )

        logger.info("ML analyze_project finished successfully")

        if isinstance(result, dict):
            logger.info(f"result_keys={list(result.keys())}")
            logger.info(f"found_sections={result.get('found_sections', [])}")
            logger.info(f"missing_sections={result.get('missing_sections', [])}")
            logger.info(f"images_count={len(result.get('images', []))}")

        return result

    except Exception as exc:
        logger.error(f"ML analyze_project failed: {exc}")
        raise