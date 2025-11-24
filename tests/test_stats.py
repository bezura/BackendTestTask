import pytest

import app.services.pr_service as pr_service_module


@pytest.mark.asyncio
async def test_stats_counts(client, monkeypatch):
    await client.post("/api/v1/team/add", json={
        "team_name": "backend",
        "members": [
            {"user_id": "u1", "username": "Alice", "is_active": True},
            {"user_id": "u2", "username": "Bob", "is_active": True},
            {"user_id": "u3", "username": "Cathy", "is_active": True},
        ],
    })

    monkeypatch.setattr(pr_service_module.random, "sample", lambda seq, k: ["u2", "u3"])

    await client.post("/api/v1/pullRequest/create", json={
        "pull_request_id": "pr_s1",
        "pull_request_name": "S1",
        "author_id": "u1",
    })
    await client.post("/api/v1/pullRequest/create", json={
        "pull_request_id": "pr_s2",
        "pull_request_name": "S2",
        "author_id": "u1",
    })
    await client.post("/api/v1/pullRequest/merge", json={"pull_request_id": "pr_s2"})

    r = await client.get("/api/v1/stats")
    assert r.status_code == 200
    stats = r.json()

    assignments = {x["user_id"]: x["count"] for x in stats["assignments_per_reviewer"]}
    assert assignments == {"u2": 2, "u3": 2}

    open_prs = {x["user_id"]: x["count"] for x in stats["open_prs_per_author"]}
    assert open_prs == {"u1": 1}

    merged_prs = {x["user_id"]: x["count"] for x in stats["merged_prs_per_author"]}
    assert merged_prs == {"u1": 1}

    assert stats["pr_count_by_status"]["OPEN"] == 1
    assert stats["pr_count_by_status"]["MERGED"] == 1
