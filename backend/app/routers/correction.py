import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models import Correction, CorrectionStatus, User
from app.schemas import CorrectionOut, CorrectionResult, CorrectionList
from app.services.auth import get_current_user, optional_user
from app.services.storage import save_upload, save_processed, get_file_url
from app.services.processor import CardProcessor
from app.config import get_settings

router = APIRouter(prefix="/api/corrections", tags=["Correção"])
settings = get_settings()


@router.post("/upload", response_model=CorrectionOut, status_code=201)
async def upload_correction(
    file: UploadFile = File(...),
    student_name: str = Form(...),
    student_id: str = Form(...),
    class_name: str = Form(...),
    discipline: str = Form(""),
    current_user: Optional[User] = Depends(optional_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")

    contents = await file.read()
    if len(contents) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Arquivo excede {settings.max_file_size_mb}MB")

    original_path = await save_upload(contents, file.filename, settings.upload_dir)

    correction = Correction(
        teacher_id=current_user.id if current_user else "anonymous",
        student_name=student_name,
        student_id=student_id,
        class_name=class_name,
        discipline=discipline,
        original_filename=file.filename or "captura.jpg",
        original_path=original_path,
        file_size_bytes=len(contents),
        status=CorrectionStatus.PENDING,
    )
    db.add(correction)
    await db.commit()
    await db.refresh(correction)
    return correction


@router.post("/{correction_id}/process", response_model=CorrectionResult)
async def process_correction(
    correction_id: str,
    gabarito: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(optional_user),
):
    result = await db.execute(select(Correction).where(Correction.id == correction_id))
    correction = result.scalar_one_or_none()
    if not correction:
        raise HTTPException(status_code=404, detail="Correção não encontrada")

    correction.status = CorrectionStatus.PROCESSING
    correction.updated_at = datetime.utcnow()
    await db.commit()

    try:
        answer_key = None
        if gabarito:
            answer_key = json.loads(gabarito)

        processor = CardProcessor(correction.original_path)
        process_result = processor.process(gabarito=answer_key)

        processed_bytes = processor.get_processed_bytes()
        processed_path = await save_processed(processed_bytes, correction_id, settings.processed_dir)

        correction.processed_path = processed_path
        correction.status = CorrectionStatus.COMPLETED
        correction.confidence = process_result.get("confidence")
        correction.image_width = process_result["width"]
        correction.image_height = process_result["height"]
        correction.result_json = json.dumps(process_result)
        correction.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(correction)

        return CorrectionResult(
            id=correction.id,
            status=CorrectionStatus.COMPLETED,
            confidence=correction.confidence,
            answers=process_result.get("answers"),
            details=process_result.get("details"),
            total_questions=process_result.get("total_questions"),
            correct_answers=process_result.get("correct_answers"),
            score=process_result.get("score"),
            processed_image_url=get_file_url(processed_path),
        )

    except Exception as e:
        correction.status = CorrectionStatus.FAILED
        correction.error_message = str(e)
        correction.updated_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(status_code=422, detail=f"Erro no processamento: {str(e)}")


@router.get("/{correction_id}", response_model=CorrectionOut)
async def get_correction(
    correction_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Correction).where(Correction.id == correction_id))
    correction = result.scalar_one_or_none()
    if not correction:
        raise HTTPException(status_code=404, detail="Correção não encontrada")
    return correction


@router.get("/{correction_id}/result", response_model=CorrectionResult)
async def get_result(correction_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Correction).where(Correction.id == correction_id))
    correction = result.scalar_one_or_none()
    if not correction:
        raise HTTPException(status_code=404, detail="Correção não encontrada")

    parsed = json.loads(correction.result_json) if correction.result_json else {}
    return CorrectionResult(
        id=correction.id,
        status=correction.status,
        confidence=correction.confidence,
        answers=parsed.get("answers"),
        details=parsed.get("details"),
        total_questions=parsed.get("total_questions"),
        correct_answers=parsed.get("correct_answers"),
        score=parsed.get("score"),
        processed_image_url=get_file_url(correction.processed_path) if correction.processed_path else None,
        error_message=correction.error_message,
    )


@router.get("", response_model=CorrectionList)
async def list_corrections(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[CorrectionStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(optional_user),
):
    query = select(Correction)
    if current_user:
        query = query.where(Correction.teacher_id == current_user.id)
    if status_filter:
        query = query.where(Correction.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(desc(Correction.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return CorrectionList(items=items, total=total, page=page, page_size=page_size)
