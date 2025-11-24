import pytest


@pytest.mark.asyncio
async def test_team_add_duplicate_should_return_team_exists(client):
    payload = {
        "team_name": "backend",
        "members": [
            {"user_id": "u1", "username": "Alice", "is_active": True},
            {"user_id": "u2", "username": "Bob", "is_active": True},
        ],
    }

    # первый вызов — создаёт команду
    r1 = await client.post("/api/v1/team/add", json=payload)
    assert r1.status_code == 201

    # второй — должен вернуть 400 TEAM_EXISTS
    r2 = await client.post("/api/v1/team/add", json=payload)
    assert r2.status_code == 400

    body = r2.json()
    assert body["detail"]["error"]["code"] == "TEAM_EXISTS"
