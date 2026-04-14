from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.claims import router as claims_router
from app.api.routes.documents import router as documents_router
from app.api.routes.evals import router as evals_router
from app.api.routes.review import router as review_router
from app.api.routes.workflow import router as workflow_router
from app.config import get_settings
from app.db import init_db

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Hybrid multi-agent claims adjudication platform for auto and healthcare domains.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


app.include_router(claims_router)
app.include_router(documents_router)
app.include_router(workflow_router)
app.include_router(review_router)
app.include_router(evals_router)