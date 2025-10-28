# run_server.py
import uvicorn, os
from datetime import datetime

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    uvicorn.run(
        "server.api.ingest:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=False,
        access_log=True,
        log_level="info",
        workers=1,
    )
