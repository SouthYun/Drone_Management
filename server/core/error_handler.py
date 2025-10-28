# server/core/error_handler.py
"""
Global Error & Exception Handler
--------------------------------
FastAPI 전역 예외를 JSON 형태로 통일하고 콘솔/파일 로그를 남긴다.
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

# ────────────────────────────────
# Logger 기본 설정
# ────────────────────────────────
logger = logging.getLogger("drowni.server")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("logs/error.log")
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# ────────────────────────────────
# 미들웨어 (요청 처리 전후 로깅)
# ────────────────────────────────
class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.exception(f"Unhandled error in {request.url.path}: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error"},
            )

# ────────────────────────────────
# FastAPI 이벤트 핸들러 등록 함수
# ────────────────────────────────
def register_exception_handlers(app):
    """FastAPI 앱에 전역 예외 핸들러와 로깅 미들웨어 등록"""

    app.add_middleware(ErrorLoggingMiddleware)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTP {exc.status_code} @ {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "path": request.url.path},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error @ {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Invalid request payload", "details": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception @ {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error"},
        )

    return app
