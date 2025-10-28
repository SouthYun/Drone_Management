# server/security/auth.py
"""
Simple API Key Auth
-------------------
관리자 요청 보호용 미들웨어
"""

import os
from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader

ADMIN_KEY = os.getenv("ADMIN_API_KEY", "drowni-secret-key")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(request: Request, api_key: str = None):
    """요청 헤더의 X-API-Key 검증"""
    key = api_key or request.headers.get("X-API-Key")
    if not key or key != ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
