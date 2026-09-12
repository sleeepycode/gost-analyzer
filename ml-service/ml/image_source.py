
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

from ml.logger import logger


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https")


def is_backend_relative_path(value: str) -> bool:
    return value.startswith("/storage/") or value.startswith("storage/")


def build_backend_url(path: str) -> str:
    backend_base_url = os.getenv("BACKEND_BASE_URL", "").strip()

    if not backend_base_url:
        logger.warning(
            "BACKEND_BASE_URL is not set, relative backend image path cannot be downloaded as URL"
        )
        return path

    normalized_path = path if path.startswith("/") else "/" + path
    full_url = urljoin(backend_base_url.rstrip("/") + "/", normalized_path.lstrip("/"))

    logger.info(f"Backend relative image path converted to URL: {path} -> {full_url}")

    return full_url


def download_image_url(url: str, timeout: int | None = None) -> str:
    timeout = timeout or int(os.getenv("IMAGE_DOWNLOAD_TIMEOUT", "15"))
    logger.info(f"Image download started: {url}")

    try:
        response = requests.get(url, timeout=(5, timeout), stream=True)
        logger.info(f"Image download response status={response.status_code} url={url}")
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error(f"Image download timeout: {url}")
        raise
    except requests.exceptions.ConnectionError as exc:
        logger.error(f"Image download connection error: {url}; error={exc}")
        raise
    except requests.exceptions.HTTPError as exc:
        logger.error(f"Image download HTTP error: {url}; status={getattr(response, 'status_code', None)}; error={exc}")
        raise
    except requests.exceptions.RequestException as exc:
        logger.error(f"Image download request error: {url}; error={exc}")
        raise

    content_type = response.headers.get("content-type", "")
    logger.info(f"Image download content-type={content_type}")

    suffix = ".img"
    if "png" in content_type:
        suffix = ".png"
    elif "jpeg" in content_type or "jpg" in content_type:
        suffix = ".jpg"
    elif "webp" in content_type:
        suffix = ".webp"

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="ml_image_url_")
    total_bytes = 0

    try:
        with temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
                    total_bytes += len(chunk)
        logger.info(f"Image downloaded to temp file: {temp_file.name}; bytes={total_bytes}")
        if total_bytes == 0:
            logger.warning(f"Downloaded image is empty: {url}")
        return temp_file.name
    except Exception as exc:
        logger.error(f"Failed to write downloaded image to temp file: {exc}")
        Path(temp_file.name).unlink(missing_ok=True)
        raise


@contextmanager
def resolve_image_path(path_or_url: str):
    logger.info(f"Resolving image source: {path_or_url}")

    temp_path = None

    if not path_or_url:
        logger.error("Empty image path/url received")
        raise ValueError("Empty image path/url received")

    source = path_or_url

    if is_backend_relative_path(source):
        source = build_backend_url(source)

    if is_url(source):
        temp_path = download_image_url(source)
        try:
            yield temp_path
        finally:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)
                logger.info(f"Temporary downloaded image removed: {temp_path}")
    else:
        local_path = Path(source)

        if not local_path.exists():
            logger.warning(f"Local image path does not exist: {source}")

        logger.info(f"Using local image path: {source}")
        yield source
