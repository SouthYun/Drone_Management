# run_server.py
"""
DrownI API 서버 실행 스크립트
----------------------------
- uvicorn 기반으로 server.api.ingest:app 실행
- 로그 출력 및 graceful shutdown 지원
"""

import uvicorn
import os
from datetime import datetime

if __name__ == "__main__":
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(
        log_dir,
        f"drowni_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    )

    uvicorn.run(
        "server.api.ingest:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=False,          # 개발 시 True
        access_log=True,
        log_level="info",
        workers=1,
    )
