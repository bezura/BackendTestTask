import pytest

TEAM_PAYLOAD = {
    "team_name": "backend",
    "members": [
        {"user_id": "u1", "username": "Alice", "is_active": True},
        {"user_id": "u2", "username": "Bob", "is_active": True},
        {"user_id": "u3", "username": "Cathy", "is_active": True},
    ],
}


@pytest.mark.asyncio
async def test_users_set_is_active_changes_flag(client):
    await client.post("/api/v1/team/add", json=TEAM_PAYLOAD)

    r = await client.post("/api/v1/users/setIsActive", json={"user_id": "u2", "is_active": False})
    assert r.status_code == 200
    user = r.json()["user"]
    assert user["user_id"] == "u2"
    assert user["is_active"] is False


@pytest.mark.asyncio
async def test_users_set_is_active_not_found(client):
    r = await client.post("/api/v1/users/setIsActive", json={"user_id": "nope", "is_active": False})
    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_users_get_review_empty_list(client):
    await client.post("/api/v1/team/add", json=TEAM_PAYLOAD)

    r = await client.get("/api/v1/users/getReview", params={"user_id": "u2"})
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == "u2"
    assert body["pull_requests"] == []


@pytest.mark.asyncio
async def test_users_get_review_user_not_found(client):
    r = await client.get("/api/v1/users/getReview", params={"user_id": "missing"})
    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "NOT_FOUND"
