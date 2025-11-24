import pytest

import app.services.pr_service as pr_service_module


@pytest.mark.asyncio
async def test_pr_create_assigns_two_reviewers_when_possible(client, monkeypatch):
    await client.post(
        "/api/v1/team/add_or_update",
        json={
            "team_name": "backend",
            "members": [
                {"user_id": "u1", "username": "Alice", "is_active": True},  # author
                {"user_id": "u2", "username": "Bob", "is_active": True},
                {"user_id": "u3", "username": "Cathy", "is_active": True},
                {"user_id": "u4", "username": "Dan", "is_active": False},  # inactive
            ],
        },
    )

    # возьмем u2,u3
    monkeypatch.setattr(pr_service_module.random, "sample", lambda seq, k: ["u2", "u3"])

    r = await client.post(
        "/api/v1/pullRequest/create",
        json={
            "pull_request_id": "pr1",
            "pull_request_name": "Add feature",
            "author_id": "u1",
        },
    )

    assert r.status_code == 201
    pr = r.json()["pr"]
    assert pr["status"] == "OPEN"
    assert set(pr["assigned_reviewers"]) == {"u2", "u3"}
    assert "u1" not in pr["assigned_reviewers"]
    assert "u4" not in pr["assigned_reviewers"]


@pytest.mark.asyncio
async def test_pr_create_assigns_one_when_only_one_candidate(client, monkeypatch):
    await client.post(
        "/api/v1/team/add_or_update",
        json={
            "team_name": "backend",
            "members": [
                {"user_id": "u1", "username": "Alice", "is_active": True},  # author
                {"user_id": "u2", "username": "Bob", "is_active": True},
            ],
        },
    )

    r = await client.post(
        "/api/v1/pullRequest/create",
        json={
            "pull_request_id": "pr2",
            "pull_request_name": "One candidate",
            "author_id": "u1",
        },
    )

    pr = r.json()["pr"]
    assert pr["assigned_reviewers"] == ["u2"]


@pytest.mark.asyncio
async def test_pr_create_404_when_author_has_no_team(client):
    # автор не существует
    await client.post(
        "/api/v1/team/add_or_update",
        json={
            "team_name": "other",
            "members": [{"user_id": "uX", "username": "X", "is_active": True}],
        },
    )

    r = await client.post(
        "/api/v1/pullRequest/create",
        json={
            "pull_request_id": "pr3",
            "pull_request_name": "No team",
            "author_id": "u1",
        },
    )

    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_pr_merge_idempotent(client):
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
    await client.post(
        "/api/v1/pullRequest/create",
        json={
            "pull_request_id": "pr4",
            "pull_request_name": "To merge",
            "author_id": "u1",
        },
    )

    r1 = await client.post("/api/v1/pullRequest/merge", json={"pull_request_id": "pr4"})
    assert r1.status_code == 200
    assert r1.json()["pr"]["status"] == "MERGED"
    merged_at_first = r1.json()["pr"]["merged_at"]

    r2 = await client.post("/api/v1/pullRequest/merge", json={"pull_request_id": "pr4"})
    assert r2.status_code == 200
    assert r2.json()["pr"]["status"] == "MERGED"
    # merged_at не должен "сбрасываться"
    assert r2.json()["pr"]["merged_at"] == merged_at_first


@pytest.mark.asyncio
async def test_pr_reassign_success(client, monkeypatch):
    # team A: author u1, reviewers u2,u3,u4
    await client.post(
        "/api/v1/team/add_or_update",
        json={
            "team_name": "backend",
            "members": [
                {"user_id": "u1", "username": "Alice", "is_active": True},
                {"user_id": "u2", "username": "Bob", "is_active": True},
                {"user_id": "u3", "username": "Cathy", "is_active": True},
                {"user_id": "u4", "username": "Dan", "is_active": True},
            ],
        },
    )

    monkeypatch.setattr(pr_service_module.random, "sample", lambda seq, k: ["u2", "u3"])
    await client.post(
        "/api/v1/pullRequest/create",
        json={
            "pull_request_id": "pr5",
            "pull_request_name": "Reassign",
            "author_id": "u1",
        },
    )

    # replacement choice -> u4
    monkeypatch.setattr(pr_service_module.random, "choice", lambda seq: "u4")

    r = await client.post(
        "/api/v1/pullRequest/reassign",
        json={
            "pull_request_id": "pr5",
            "old_reviewer_id": "u2",
        },
    )

    assert r.status_code == 200
    body = r.json()
    assert body["replaced_by"] == "u4"
    assert set(body["pr"]["assigned_reviewers"]) == {"u3", "u4"}


@pytest.mark.asyncio
async def test_pr_reassign_not_assigned(client, monkeypatch):
    await client.post(
        "/api/v1/team/add_or_update",
        json={
            "team_name": "backend",
            "members": [
                {"user_id": "u1", "username": "Alice", "is_active": True},
                {"user_id": "u2", "username": "Bob", "is_active": True},
                {"user_id": "u3", "username": "Cathy", "is_active": True},
            ],
        },
    )
    monkeypatch.setattr(pr_service_module.random, "sample", lambda seq, k: ["u2", "u3"])
    await client.post(
        "/api/v1/pullRequest/create",
        json={
            "pull_request_id": "pr6",
            "pull_request_name": "Reassign bad",
            "author_id": "u1",
        },
    )

    r = await client.post(
        "/api/v1/pullRequest/reassign",
        json={
            "pull_request_id": "pr6",
            "old_reviewer_id": "u999",
        },
    )

    assert r.status_code == 409
    assert r.json()["detail"]["error"]["code"] == "NOT_ASSIGNED"


@pytest.mark.asyncio
async def test_pr_reassign_no_candidate(client, monkeypatch):
    # team: author u1, reviewer u2 only
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

    await client.post(
        "/api/v1/pullRequest/create",
        json={
            "pull_request_id": "pr7",
            "pull_request_name": "No candidate",
            "author_id": "u1",
        },
    )

    r = await client.post(
        "/api/v1/pullRequest/reassign",
        json={
            "pull_request_id": "pr7",
            "old_reviewer_id": "u2",
        },
    )

    assert r.status_code == 409
    assert r.json()["detail"]["error"]["code"] == "NO_CANDIDATE"


@pytest.mark.asyncio
async def test_pr_reassign_after_merge_forbidden(client, monkeypatch):
    await client.post(
        "/api/v1/team/add_or_update",
        json={
            "team_name": "backend",
            "members": [
                {"user_id": "u1", "username": "Alice", "is_active": True},
                {"user_id": "u2", "username": "Bob", "is_active": True},
                {"user_id": "u3", "username": "Cathy", "is_active": True},
            ],
        },
    )
    monkeypatch.setattr(pr_service_module.random, "sample", lambda seq, k: ["u2", "u3"])
    await client.post(
        "/api/v1/pullRequest/create",
        json={
            "pull_request_id": "pr8",
            "pull_request_name": "Merge then reassign",
            "author_id": "u1",
        },
    )
    await client.post("/api/v1/pullRequest/merge", json={"pull_request_id": "pr8"})

    r = await client.post(
        "/api/v1/pullRequest/reassign",
        json={
            "pull_request_id": "pr8",
            "old_reviewer_id": "u2",
        },
    )

    assert r.status_code == 409
    assert r.json()["detail"]["error"]["code"] == "PR_MERGED"
