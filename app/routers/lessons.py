from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionDep
from app.models import Lesson, LessonStatus
from app.routers.tutors import get_tutor_or_404
from app.schemas import LessonCreate, LessonPage, LessonRead

router = APIRouter(prefix="/lessons", tags=["lessons"])


async def get_lesson_or_404(lesson_id: int, session: AsyncSession) -> Lesson:
    lesson = await session.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lesson not found")
    return lesson


async def has_overlap(session: AsyncSession, data: LessonCreate) -> bool:
    query = select(Lesson.id).where(
        Lesson.tutor_id == data.tutor_id,
        Lesson.status != LessonStatus.CANCELLED,
        Lesson.starts_at < data.ends_at,
        Lesson.ends_at > data.starts_at,
    )
    return await session.scalar(query) is not None


@router.post("", response_model=LessonRead, status_code=status.HTTP_201_CREATED)
async def create_lesson(data: LessonCreate, session: SessionDep):
    await get_tutor_or_404(data.tutor_id, session)
    if await has_overlap(session, data):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Tutor already has a lesson overlapping this time slot",
        )
    lesson = Lesson(**data.model_dump())
    session.add(lesson)
    await session.commit()
    await session.refresh(lesson)
    return lesson


@router.get("", response_model=LessonPage)
async def list_lessons(
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tutor_id: int | None = None,
    status_filter: str | None = Query(None, alias="status"),
    starts_after: datetime | None = None,
    starts_before: datetime | None = None,
):
    query = select(Lesson)
    if tutor_id is not None:
        query = query.where(Lesson.tutor_id == tutor_id)
    if status_filter is not None:
        query = query.where(Lesson.status == status_filter)
    if starts_after is not None:
        query = query.where(Lesson.starts_at >= starts_after)
    if starts_before is not None:
        query = query.where(Lesson.starts_at <= starts_before)
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = await session.scalars(query.order_by(Lesson.starts_at).limit(limit).offset(offset))
    return LessonPage(total=total or 0, limit=limit, offset=offset, items=list(rows))


@router.get("/{lesson_id}", response_model=LessonRead)
async def get_lesson(lesson_id: int, session: SessionDep):
    return await get_lesson_or_404(lesson_id, session)


@router.patch("/{lesson_id}/cancel", response_model=LessonRead)
async def cancel_lesson(lesson_id: int, session: SessionDep):
    lesson = await get_lesson_or_404(lesson_id, session)
    if lesson.status == LessonStatus.COMPLETED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Completed lesson cannot be cancelled")
    lesson.status = LessonStatus.CANCELLED
    await session.commit()
    await session.refresh(lesson)
    return lesson


@router.patch("/{lesson_id}/complete", response_model=LessonRead)
async def complete_lesson(lesson_id: int, session: SessionDep):
    lesson = await get_lesson_or_404(lesson_id, session)
    if lesson.status != LessonStatus.SCHEDULED:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Only scheduled lessons can be completed, got {lesson.status}",
        )
    lesson.status = LessonStatus.COMPLETED
    await session.commit()
    await session.refresh(lesson)
    return lesson
