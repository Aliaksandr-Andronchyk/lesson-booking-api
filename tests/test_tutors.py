from httpx import AsyncClient


async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_create_and_get_tutor(client: AsyncClient, tutor: dict):
    response = await client.get(f"/tutors/{tutor['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Anna Petrova"
    assert body["email"] == "anna@example.com"
    assert body["subject"] == "math"


async def test_duplicate_email_conflict(client: AsyncClient, tutor: dict):
    response = await client.post(
        "/tutors",
        json={"name": "Other", "email": "anna@example.com", "subject": "physics"},
    )
    assert response.status_code == 409


async def test_invalid_email_rejected(client: AsyncClient):
    response = await client.post(
        "/tutors",
        json={"name": "Bad", "email": "not-an-email", "subject": "math"},
    )
    assert response.status_code == 422


async def test_list_tutors_pagination_and_filter(client: AsyncClient):
    for i in range(3):
        subject = "math" if i < 2 else "physics"
        response = await client.post(
            "/tutors",
            json={"name": f"Tutor {i}", "email": f"t{i}@example.com", "subject": subject},
        )
        assert response.status_code == 201

    response = await client.get("/tutors", params={"limit": 2, "offset": 0})
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2

    response = await client.get("/tutors", params={"subject": "physics"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["subject"] == "physics"


async def test_get_missing_tutor_404(client: AsyncClient):
    response = await client.get("/tutors/999")
    assert response.status_code == 404


async def test_delete_tutor(client: AsyncClient, tutor: dict):
    response = await client.delete(f"/tutors/{tutor['id']}")
    assert response.status_code == 204
    response = await client.get(f"/tutors/{tutor['id']}")
    assert response.status_code == 404
