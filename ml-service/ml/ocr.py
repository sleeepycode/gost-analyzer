from __future__ import annotations

import warnings
from pathlib import Path

from PIL import Image, ImageEnhance

from ml.image_source import resolve_image_path
from ml.logger import logger


warnings.filterwarnings("ignore", category=UserWarning)

_paddle_reader = None
_easy_reader = None


def prepare_image_for_ocr(image_path: str) -> str:
    """
    Готовит изображение для OCR и сохраняет рядом временный preprocessed-файл.
    EasyOCR лучше принимает путь к файлу, а не PIL.Image.
    """
    image_path = str(image_path)

    image = Image.open(image_path).convert("L")

    width, height = image.size
    image = image.resize((width * 2, height * 2))

    image = ImageEnhance.Contrast(image).enhance(1.7)
    image = ImageEnhance.Sharpness(image).enhance(1.8)

    source = Path(image_path)
    prepared_path = source.with_name(f"{source.stem}_prepared{source.suffix}")

    image.save(prepared_path)

    return str(prepared_path)


def get_paddle_reader():
    global _paddle_reader

    if _paddle_reader is None:
        from paddleocr import PaddleOCR

        logger.info("[OCR] Initializing PaddleOCR...")

        _paddle_reader = PaddleOCR(
            lang="ru",
            use_angle_cls=True,
        )

    return _paddle_reader


def get_easy_reader():
    global _easy_reader

    if _easy_reader is None:
        import easyocr

        logger.info("[OCR] Initializing EasyOCR fallback...")
        _easy_reader = easyocr.Reader(["ru", "en"], gpu=False)

    return _easy_reader


def extract_text_paddle(image_path: str) -> str:
    image_path = str(image_path)

    reader = get_paddle_reader()

    result = reader.ocr(image_path)

    lines: list[str] = []

    if not result:
        return ""

    for page in result:
        if not page:
            continue

        for item in page:
            text = _extract_text_from_paddle_item(item)

            if text:
                lines.append(text)

    return " ".join(lines).strip()


def _extract_text_from_paddle_item(item) -> str:
    if not item:
        return ""

    if isinstance(item, str):
        return item.strip()

    if isinstance(item, (list, tuple)):
        if len(item) >= 2:
            text_data = item[1]

            if isinstance(text_data, str):
                return text_data.strip()

            if isinstance(text_data, (list, tuple)) and text_data:
                if isinstance(text_data[0], str):
                    return text_data[0].strip()

        for sub_item in item:
            text = _extract_text_from_paddle_item(sub_item)

            if text:
                return text

    return ""


def extract_text_easy(image_path: str) -> str:
    image_path = str(image_path)

    prepared_path = None

    try:
        prepared_path = prepare_image_for_ocr(image_path)

        reader = get_easy_reader()

        result = reader.readtext(
            prepared_path,
            detail=0
        )

        result = [
            line.strip()
            for line in result
            if line and line.strip()
        ]

        return " ".join(result).strip()

    finally:
        if prepared_path:
            try:
                Path(prepared_path).unlink(missing_ok=True)
            except Exception as exc:
                logger.warning(
                    f"Could not remove prepared OCR image: {exc}"
                )


def _extract_text_from_image_raw(local_image_path: str) -> str:
    local_image_path = str(local_image_path)

    path = Path(local_image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Image not found: {local_image_path}"
        )

    paddle_error = None
    easy_error = None

    try:
        text = extract_text_paddle(str(path))

        if text.strip():
            logger.info(
                f"[OCR] PaddleOCR text from {path.name}: {text[:300]}"
            )

            return text

        logger.warning(
            f"[OCR FALLBACK] PaddleOCR returned empty text for {path.name}"
        )

    except Exception as error:
        paddle_error = error

        logger.warning(
            f"[OCR FALLBACK] PaddleOCR failed for {path.name}: {error}"
        )

    try:
        text = extract_text_easy(str(path))

        if text.strip():
            logger.info(
                f"[OCR] EasyOCR text from {path.name}: {text[:300]}"
            )

            return text

        logger.warning(
            f"[OCR FALLBACK] EasyOCR returned empty text for {path.name}"
        )

    except Exception as error:
        easy_error = error

        logger.error(
            f"[OCR ERROR] EasyOCR failed for {path.name}: {error}"
        )

    logger.error(
        "[OCR ERROR] All OCR engines failed. "
        f"PaddleOCR error: {paddle_error}; "
        f"EasyOCR error: {easy_error}"
    )

    return ""


def extract_text_from_image(image_path: str) -> str:
    image_path = str(image_path)

    logger.info(
        f"OCR pipeline started for image source: {image_path}"
    )

    try:
        with resolve_image_path(image_path) as local_image_path:
            local_image_path = str(local_image_path)

            logger.info(
                f"OCR local resolved path: {local_image_path}"
            )

            text = _extract_text_from_image_raw(local_image_path)

            logger.info(
                f"OCR pipeline finished text_len={len(text or '')}"
            )

            if not text:
                logger.warning("OCR result is empty")

            return text

    except Exception as exc:
        logger.error(
            f"OCR pipeline failed for {image_path}: {exc}"
        )

        raise