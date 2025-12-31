import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool

from .config import Settings
from .sheets_client import SheetsClient

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"

settings = Settings.from_env()
client = SheetsClient(settings)

app = FastAPI(title="Sheets Aggregation Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")


def _serialize_datetime(value: datetime.datetime | None) -> str | None:
    if value is None:
        return None
    return value.replace(tzinfo=datetime.timezone.utc).isoformat()


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "last_fetched": _serialize_datetime(client.last_fetched),
        "configured_sheets": len(settings.sheet_urls),
    }


@app.get("/combined")
async def combined() -> List[Dict[str, Any]]:
    try:
        data = await run_in_threadpool(client.fetch_combined_rows)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    return data


@app.post("/refresh")
async def refresh() -> JSONResponse:
    try:
        data = await run_in_threadpool(client.fetch_combined_rows, True)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "status": "refreshed",
            "rows": len(data),
            "last_fetched": _serialize_datetime(client.last_fetched),
        },
    )


@app.get("/")
async def root() -> Response:
    html = PUBLIC_DIR.joinpath("index.html").read_text(encoding="utf-8")
    return Response(content=html, media_type="text/html")
