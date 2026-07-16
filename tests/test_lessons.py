from httpx import AsyncClient

LESSON = {
    "student_name": "Ivan",
    "starts_at": "2026-08-01T10:00:00",
    "ends_at": "2026-08-01T11:00:00",
    "price": 25.0,
}


async def create_lesson(client: AsyncClient, tutor_id: int, **overrides) -> dict:
    payload = {**LESSON, "tutor_id": tutor_id, **overrides}
    response = await client.post("/lessons", json=payload)
    return response


async def test_create_lesson(client: AsyncClient, tutor: dict):
    response = await create_lesson(client, tutor["id"])
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "scheduled"
    assert body["tutor_id"] == tutor["id"]


async def test_lesson_for_missing_tutor_404(client: AsyncClient):
    response = await create_lesson(client, 999)
    assert response.status_code == 404


async def test_invalid_time_range_rejected(client: AsyncClient, tutor: dict):
    response = await create_lesson(
        client,
        tutor["id"],
        starts_at="2026-08-01T11:00:00",
        ends_at="2026-08-01T10:00:00",
    )
    assert response.status_code == 422


async def test_overlapping_lesson_conflict(client: AsyncClient, tutor: dict):
    assert (await create_lesson(client, tutor["id"])).status_code == 201
    # Overlaps 10:30–11:30 with existing 10:00–11:00
    response = await create_lesson(
        client,
        tutor["id"],
        starts_at="2026-08-01T10:30:00",
        ends_at="2026-08-01T11:30:00",
    )
    assert response.status_code == 409


async def test_back_to_back_lessons_allowed(client: AsyncClient, tutor: dict):
    assert (await create_lesson(client, tutor["id"])).status_code == 201
    response = await create_lesson(
        client,
        tutor["id"],
        starts_at="2026-08-01T11:00:00",
        ends_at="2026-08-01T12:00:00",
    )
    assert response.status_code == 201


async def test_cancelled_slot_can_be_rebooked(client: AsyncClient, tutor: dict):
    first = await create_lesson(client, tutor["id"])
    lesson_id = first.json()["id"]
    response = await client.patch(f"/lessons/{lesson_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    response = await create_lesson(client, tutor["id"], student_name="Maria")
    assert response.status_code == 201


async def test_completed_lesson_cannot_be_cancelled(client: AsyncClient, tutor: dict):
    lesson_id = (await create_lesson(client, tutor["id"])).json()["id"]
    response = await client.patch(f"/lessons/{lesson_id}/complete")
    assert response.status_code == 200
    response = await client.patch(f"/lessons/{lesson_id}/cancel")
    assert response.status_code == 409


async def test_list_lessons_filters(client: AsyncClient, tutor: dict):
    await create_lesson(client, tutor["id"])
    await create_lesson(
        client,
        tutor["id"],
        starts_at="2026-08-02T10:00:00",
        ends_at="2026-08-02T11:00:00",
    )

    response = await client.get("/lessons", params={"tutor_id": tutor["id"]})
    assert response.json()["total"] == 2

    response = await client.get("/lessons", params={"starts_after": "2026-08-02T00:00:00"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["starts_at"].startswith("2026-08-02")

    response = await client.get("/lessons", params={"status": "cancelled"})
    assert response.json()["total"] == 0
