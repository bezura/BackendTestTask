import pytest

import app.services.pr_service as pr_service_module
import app.services.team_service as team_service_module


@pytest.mark.asyncio
async def test_team_deactivate_users_reassigns_open_pr_reviewers(client, monkeypatch):
    # backend team: author u1, reviewers u2,u3,u4
    await client.post(
        "/api/v1/team/add_or_update",
        json={
            "team_name": "backend",
            "members": [
                {"user_id": "u1", "username": "Alice", "is_active": True},  # author
                {"user_id": "u2", "username": "Bob", "is_active": True},  # will deactivate
                {"user_id": "u3", "username": "Cathy", "is_active": True},  # stays reviewer
                {"user_id": "u4", "username": "Dan", "is_active": True},  # replacement
            ],
        },
    )

    monkeypatch.setattr(pr_service_module.random, "sample", lambda seq, k: ["u2", "u3"])

    r_create = await client.post(
        "/api/v1/pullRequest/create",
        json={
            "pull_request_id": "pr_d1",
            "pull_request_name": "Deactivate + reassign",
            "author_id": "u1",
        },
    )
    assert r_create.status_code in (200, 201)
    assert set(r_create.json()["pr"]["assigned_reviewers"]) == {"u2", "u3"}

    # replacement choice deterministic -> u4
    monkeypatch.setattr(team_service_module.random, "choice", lambda seq: "u4")

    r_deact = await client.post(
        "/api/v1/team/deactivateUsers",
        json={
            "team_name": "backend",
            "user_ids": ["u2"],
        },
    )
    assert r_deact.status_code == 200
    body = r_deact.json()
    assert body["team_name"] == "backend"
    assert set(body["deactivated"]) == {"u2"}
    assert body["reassigned_prs"] == 1

    # u2 should have zero reviews
    r_u2 = await client.get("/api/v1/users/getReview", params={"user_id": "u2"})
    assert r_u2.status_code == 200
    assert r_u2.json()["pull_requests"] == []

    # u4 should now have pr_d1 in review list
    r_u4 = await client.get("/api/v1/users/getReview", params={"user_id": "u4"})
    assert r_u4.status_code == 200
    pr_ids_u4 = {pr["pull_request_id"] for pr in r_u4.json()["pull_requests"]}
    assert "pr_d1" in pr_ids_u4

    # u3 must still be reviewer for pr_d1
    r_u3 = await client.get("/api/v1/users/getReview", params={"user_id": "u3"})
    assert r_u3.status_code == 200
    pr_ids_u3 = {pr["pull_request_id"] for pr in r_u3.json()["pull_requests"]}
    assert "pr_d1" in pr_ids_u3


@pytest.mark.asyncio
async def test_team_deactivate_users_safe_when_no_candidates(client, monkeypatch):
    # team: author u1, only reviewer candidate u2
    await client.post(
        "/api/v1/team/add_or_update",
        json={
            "team_name": "backend",
            "members": [
                {"user_id": "u1", "username": "Alice", "is_active": True},
                {"user_id": "u2", "username": "Bob", "is_active": True},
            ],
        },
    )

    # create PR assigns u2 as only reviewer
    r_create = await client.post(
        "/api/v1/pullRequest/create",
        json={
            "pull_request_id": "pr_d2",
            "pull_request_name": "No candidates",
            "author_id": "u1",
        },
    )
    assert r_create.status_code in (200, 201)
    assert r_create.json()["pr"]["assigned_reviewers"] == ["u2"]

    # deactivate u2 -> no active candidates to replace, should be safe
    r_deact = await client.post(
        "/api/v1/team/deactivateUsers",
        json={
            "team_name": "backend",
            "user_ids": ["u2"],
        },
    )
    assert r_deact.status_code == 200
    body = r_deact.json()
    assert set(body["deactivated"]) == {"u2"}
    assert body["reassigned_prs"] == 0

    # u2 should have no reviews
    r_u2 = await client.get("/api/v1/users/getReview", params={"user_id": "u2"})
    assert r_u2.status_code == 200
    assert r_u2.json()["pull_requests"] == []

    r_reassign = await client.post(
        "/api/v1/pullRequest/reassign",
        json={
            "pull_request_id": "pr_d2",
            "old_reviewer_id": "u2",
        },
    )
    assert r_reassign.status_code == 409
    assert r_reassign.json()["detail"]["error"]["code"] in ("NOT_ASSIGNED", "NO_CANDIDATE")


@pytest.mark.asyncio
async def test_team_deactivate_users_team_not_found(client):
    r = await client.post(
        "/api/v1/team/deactivateUsers",
        json={
            "team_name": "missing",
            "user_ids": ["u1"],
        },
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "NOT_FOUND"
