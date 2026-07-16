from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class TutorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    subject: str = Field(min_length=1, max_length=120)


class TutorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    subject: str
    created_at: datetime


class LessonCreate(BaseModel):
    tutor_id: int
    student_name: str = Field(min_length=1, max_length=120)
    starts_at: datetime
    ends_at: datetime
    price: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_time_range(self) -> "LessonCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class LessonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tutor_id: int
    student_name: str
    starts_at: datetime
    ends_at: datetime
    price: float
    status: str
    created_at: datetime


class Page(BaseModel):
    total: int
    limit: int
    offset: int


class TutorPage(Page):
    items: list[TutorRead]


class LessonPage(Page):
    items: list[LessonRead]
