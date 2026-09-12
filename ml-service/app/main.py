
import time
import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ml.logger import logger, short_value

try:
    from ml.api_adapter import analyze_project_payload
except Exception as import_error:
    analyze_project_payload = None
    logger.error(f"Failed to import analyze_project_payload: {import_error}")

try:
    from ml.service import analyze_project
except Exception as import_error:
    analyze_project = None
    logger.error(f"Failed to import analyze_project: {import_error}")


app = FastAPI(
    title="AI Report ML Module",
    description="ML API for report structure analysis, OCR, image classification and insert instructions",
    version="1.0.0",
)


class ImageItem(BaseModel):
    image_id: str | None = None
    path: str
    source: str | None = None


class AnalyzeRequest(BaseModel):
    project_id: str | None = None
    document_text: str = ""
    image_paths: list[str] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
    images: list[ImageItem] = Field(default_factory=list)
    topic: str = "лабораторная работа"


class StructureRequest(BaseModel):
    document_text: str
    topic: str = "лабораторная работа"


class OcrRequest(BaseModel):
    image_path: str


class ClassifyImageRequest(BaseModel):
    image_path: str


class CaptionRequest(BaseModel):
    image_type: str
    ocr_text: str = ""
    topic: str = "лабораторная работа"


@app.on_event("startup")
async def startup_event():
    logger.info("==================================================")
    logger.info("ML FastAPI server startup")
    logger.info("Available endpoints:")
    logger.info("GET  /health")
    logger.info("POST /analyze")
    logger.info("POST /analyze-structure")
    logger.info("POST /ocr")
    logger.info("POST /classify-image")
    logger.info("POST /generate-caption")
    logger.info("Swagger UI: /docs")
    logger.info("==================================================")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    started = time.time()

    logger.info(f"REQUEST START {request.method} {request.url.path}")

    try:
        response = await call_next(request)
    except Exception as exc:
        duration = time.time() - started
        logger.error(f"REQUEST CRASH {request.method} {request.url.path} after {duration:.3f}s: {exc}")
        logger.error(traceback.format_exc())
        raise

    duration = time.time() - started

    if response.status_code >= 400:
        logger.warning(
            f"REQUEST END {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.3f}s"
        )
    else:
        logger.info(
            f"REQUEST END {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.3f}s"
        )

    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body_text = ""

    try:
        raw_body = await request.body()
        body_text = raw_body.decode("utf-8", errors="replace")
    except Exception as body_error:
        body_text = f"<could not read body: {body_error}>"

    logger.warning("422 VALIDATION ERROR")
    logger.warning(f"Endpoint: {request.method} {request.url.path}")
    logger.warning(f"Validation details: {exc.errors()}")
    logger.warning(f"Request body: {short_value(body_text, 1500)}")

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "status": "validation_error",
            "message": "Request validation failed. Check required fields and field types.",
            "details": exc.errors(),
            "example": {
                "project_id": "123",
                "document_text": "Введение... Практическая часть...",
                "image_paths": ["storage/projects/123/images/graph.png"],
                "image_urls": ["http://127.0.0.1:8000/storage/projects/123/images/graph.png"],
                "images": [
                    {
                        "image_id": "img_001",
                        "path": "/storage/projects/123/images/graph.png",
                        "source": "back2_parsed_from_docx",
                    }
                ],
                "topic": "Лабораторная работа",
            },
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("500 INTERNAL SERVER ERROR")
    logger.error(f"Endpoint: {request.method} {request.url.path}")
    logger.error(f"Error: {exc}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "status": "server_error",
            "message": str(exc),
        },
    )


@app.get("/health")
def health():
    logger.info("Health check requested")
    return {
        "status": "ok",
        "service": "ml-module",
    }


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    logger.info("Analyze request received")
    logger.info(f"project_id={request.project_id}")
    logger.info(f"document_text_len={len(request.document_text or '')}")
    logger.info(f"image_paths_count={len(request.image_paths)}")
    logger.info(f"image_urls_count={len(request.image_urls)}")
    logger.info(f"images_meta_count={len(request.images)}")
    logger.info(f"topic={request.topic}")

    payload = request.model_dump()

    try:
        if analyze_project_payload is not None:
            logger.info("Using ml.api_adapter.analyze_project_payload")
            result = analyze_project_payload(payload)
        elif analyze_project is not None:
            logger.warning("api_adapter not available, using ml.service.analyze_project directly")

            image_paths = list(request.image_paths or [])
            image_paths.extend(request.image_urls or [])

            for image in request.images or []:
                image_paths.append(image.path)

            result = analyze_project(
                document_text=request.document_text,
                image_paths=image_paths,
                topic=request.topic,
            )
        else:
            logger.error("No ML analyze function available")
            return {
                "success": False,
                "status": "error",
                "error": "ML analyze function is not available",
            }

        logger.info("Analyze pipeline completed")
        logger.info(f"result_success={result.get('success') if isinstance(result, dict) else 'unknown'}")
        logger.info(f"result_status={result.get('status') if isinstance(result, dict) else 'unknown'}")

        if isinstance(result, dict):
            logger.info(f"found_sections={result.get('found_sections', [])}")
            logger.info(f"missing_sections={result.get('missing_sections', [])}")
            logger.info(f"images_result_count={len(result.get('images', []))}")

        return result

    except Exception as exc:
        logger.error(f"Analyze pipeline failed: {exc}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "status": "error",
            "error": str(exc),
        }


@app.post("/analyze-structure")
def analyze_structure(request: StructureRequest):
    logger.info("Analyze structure request received")
    logger.info(f"document_text_len={len(request.document_text or '')}")
    logger.info(f"topic={request.topic}")

    if analyze_project is None:
        logger.error("analyze_project is not available")
        return {
            "success": False,
            "status": "error",
            "error": "analyze_project is not available",
        }

    try:
        result = analyze_project(
            document_text=request.document_text,
            image_paths=[],
            topic=request.topic,
        )

        return {
            "success": result.get("success", True) if isinstance(result, dict) else True,
            "found_sections": result.get("found_sections", []) if isinstance(result, dict) else [],
            "missing_sections": result.get("missing_sections", []) if isinstance(result, dict) else [],
            "status": "ready",
        }

    except Exception as exc:
        logger.error(f"Analyze structure failed: {exc}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "status": "error",
            "error": str(exc),
        }


@app.post("/ocr")
def ocr(request: OcrRequest):
    logger.info("OCR request received")
    logger.info(f"image_path={request.image_path}")

    try:
        from ml.ocr import extract_text_from_image

        text = extract_text_from_image(request.image_path)

        logger.info(f"OCR completed text_len={len(text or '')}")

        if not text:
            logger.warning("OCR returned empty text")

        return {
            "success": True,
            "text": text,
            "status": "ready",
        }

    except Exception as exc:
        logger.error(f"OCR failed: {exc}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "status": "error",
            "error": str(exc),
        }


@app.post("/classify-image")
def classify_image(request: ClassifyImageRequest):
    logger.info("Classify image request received")
    logger.info(f"image_path={request.image_path}")

    try:
        from ml.image_classifier import classify_image_fallback

        image_type = classify_image_fallback(request.image_path)

        logger.info(f"Image classification completed type={image_type}")

        return {
            "success": True,
            "type": image_type,
            "status": "ready",
        }

    except Exception as exc:
        logger.error(f"Image classification failed: {exc}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "status": "error",
            "error": str(exc),
        }


@app.post("/generate-caption")
def generate_caption(request: CaptionRequest):
    logger.info("Generate caption request received")
    logger.info(f"image_type={request.image_type}")
    logger.info(f"ocr_text_len={len(request.ocr_text or '')}")
    logger.info(f"topic={request.topic}")

    try:
        caption = f"Рисунок — {request.image_type}"

        if request.ocr_text:
            cleaned_text = request.ocr_text.strip().replace("\n", " ")
            caption = f"Рисунок — {request.image_type}: {cleaned_text[:80]}"

        logger.info(f"Caption generated: {caption}")

        return {
            "success": True,
            "caption": caption,
            "status": "ready",
        }

    except Exception as exc:
        logger.error(f"Caption generation failed: {exc}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "status": "error",
            "error": str(exc),
        }
