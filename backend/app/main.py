import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.alignment import router as alignment_router
from app.api.compare import router as compare_router
from app.api.contact import router as contact_router
from app.api.drift import router as drift_router
from app.api.fingerprint import router as fingerprint_router
from app.api.lookup import router as lookup_router
from app.api.metadata import router as metadata_router
from app.api.positions import router as positions_router
from app.api.search import router as search_router
from app.api.summary import router as summary_router


DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


def get_cors_origins() -> list[str]:
    configured = os.getenv("FRONTEND_ORIGINS", "")
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    return list(DEFAULT_CORS_ORIGINS) + origins


app = FastAPI(title="Political Fingerprint API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fingerprint_router)
app.include_router(positions_router)
app.include_router(alignment_router)
app.include_router(drift_router)
app.include_router(summary_router)
app.include_router(lookup_router)
app.include_router(metadata_router)
app.include_router(search_router)
app.include_router(compare_router)
app.include_router(contact_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
