from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionDep
from app.models import Tutor
from app.schemas import TutorCreate, TutorPage, TutorRead

router = APIRouter(prefix="/tutors", tags=["tutors"])


async def get_tutor_or_404(tutor_id: int, session: AsyncSession) -> Tutor:
    tutor = await session.get(Tutor, tutor_id)
    if tutor is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tutor not found")
    return tutor


@router.post("", response_model=TutorRead, status_code=status.HTTP_201_CREATED)
async def create_tutor(data: TutorCreate, session: SessionDep):
    tutor = Tutor(**data.model_dump())
    session.add(tutor)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Tutor with this email already exists"
        ) from None
    await session.refresh(tutor)
    return tutor


@router.get("", response_model=TutorPage)
async def list_tutors(
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    subject: str | None = None,
):
    query = select(Tutor)
    if subject:
        query = query.where(Tutor.subject == subject)
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = await session.scalars(query.order_by(Tutor.id).limit(limit).offset(offset))
    return TutorPage(total=total or 0, limit=limit, offset=offset, items=list(rows))


@router.get("/{tutor_id}", response_model=TutorRead)
async def get_tutor(tutor_id: int, session: SessionDep):
    return await get_tutor_or_404(tutor_id, session)


@router.delete("/{tutor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tutor(tutor_id: int, session: SessionDep):
    tutor = await get_tutor_or_404(tutor_id, session)
    await session.delete(tutor)
    await session.commit()
