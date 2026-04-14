from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.dependencies import get_db_session
from app.models.document import ClaimDocument
from app.repositories.claim_repository import ClaimRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.claims import ClaimDocumentRead
from app.services.document_parser import DocumentParser
from app.services.utils import sha256_file

router = APIRouter(tags=["documents"])


@router.post("/claims/{claim_id}/documents", response_model=ClaimDocumentRead)
async def upload_document(
    claim_id: str,
    file: UploadFile = File(...),
    document_type: str | None = Form(default=None),
    db: Session = Depends(get_db_session),
) -> ClaimDocumentRead:
    claim = ClaimRepository(db).get(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    settings = get_settings()
    upload_dir = Path(settings.upload_dir) / claim_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    parser = DocumentParser()
    parsed = parser.parse(str(file_path))
    fingerprint = sha256_file(file_path)

    existing_fingerprint = db.scalar(
        select(ClaimDocument).where(ClaimDocument.claim_id == claim_id, ClaimDocument.fingerprint == fingerprint).limit(1)
    )

    payload = {
        "claim_id": claim_id,
        "filename": file.filename,
        "mime_type": file.content_type or "application/octet-stream",
        "document_type": document_type,
        "storage_path": str(file_path),
        "ocr_text": parsed.text,
        "metadata_json": {
            **parsed.metadata,
            "duplicate_in_claim": bool(existing_fingerprint),
        },
        "fingerprint": fingerprint,
    }
    document = DocumentRepository(db).create(payload)
    return ClaimDocumentRead.model_validate(document)


@router.get("/claims/{claim_id}/documents", response_model=list[ClaimDocumentRead])
def list_documents(claim_id: str, db: Session = Depends(get_db_session)) -> list[ClaimDocumentRead]:
    if not ClaimRepository(db).get(claim_id):
        raise HTTPException(status_code=404, detail="Claim not found")
    documents = DocumentRepository(db).list_for_claim(claim_id)
    return [ClaimDocumentRead.model_validate(document) for document in documents]


@router.get("/documents/{document_id}", response_model=ClaimDocumentRead)
def get_document(document_id: str, db: Session = Depends(get_db_session)) -> ClaimDocumentRead:
    document = DocumentRepository(db).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return ClaimDocumentRead.model_validate(document)