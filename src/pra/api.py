from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .core import scan_summary


class ScanRequest(BaseModel):
    path: str = Field(..., description="File or directory to scan")


def create_app() -> FastAPI:
    app = FastAPI(title="Pattern-to-Rule Automation", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/scan")
    def scan(request: ScanRequest) -> dict:
        scan_path = Path(request.path)
        if not scan_path.exists():
            raise HTTPException(status_code=404, detail="Scan path not found")
        return scan_summary(scan_path)

    return app


app = create_app()
