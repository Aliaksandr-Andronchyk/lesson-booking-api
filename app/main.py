from fastapi import FastAPI

from app.routers import lessons, tutors

app = FastAPI(
    title="Lesson Booking API",
    description="REST API for tutors to manage students' lesson bookings.",
    version="0.1.0",
)

app.include_router(tutors.router)
app.include_router(lessons.router)


@app.get("/health", tags=["service"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
