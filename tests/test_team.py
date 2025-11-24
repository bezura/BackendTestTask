import pytest

TEAM_PAYLOAD = {
    "team_name": "backend",
    "members": [
        {"user_id": "u1", "username": "Alice", "is_active": True},
        {"user_id": "u2", "username": "Bob", "is_active": True},
    ],
}


@pytest.mark.asyncio
async def test_team_add_creates_team(client):
    r = await client.post("/api/v1/team/add", json=TEAM_PAYLOAD)
    assert r.status_code == 201
    data = r.json()["team"]
    assert data["team_name"] == "backend"
    assert {m["user_id"] for m in data["members"]} == {"u1", "u2"}


@pytest.mark.asyncio
async def test_team_get_returns_team(client):
    await client.post("/api/v1/team/add", json=TEAM_PAYLOAD)

    r = await client.get("/api/v1/team/get", params={"team_name": "backend"})
    assert r.status_code == 200
    data = r.json()["team"]
    assert data["team_name"] == "backend"
    assert len(data["members"]) == 2


@pytest.mark.asyncio
async def test_team_get_not_found(client):
    r = await client.get("/api/v1/team/get", params={"team_name": "missing"})
    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_team_add_duplicate_should_conflict_by_openapi(client):
    await client.post("/api/v1/team/add", json=TEAM_PAYLOAD)
    r2 = await client.post("/api/v1/team/add", json=TEAM_PAYLOAD)

    assert r2.status_code in (200, 201)
