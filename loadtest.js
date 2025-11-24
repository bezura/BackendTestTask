import http from "k6/http";
import {check, sleep} from "k6";

const BASE = __ENV.BASE_URL;

// ---------- k6 options ----------
export const options = {
    scenarios: {
        steady_5rps: {
            executor: "constant-arrival-rate",
            rate: 5,              // 5 итераций/сек
            timeUnit: "1s",
            duration: "2m",       // 2 минуты теста
            preAllocatedVUs: 10,
            maxVUs: 30,
        },
    },
    thresholds: {
        http_req_failed: ["rate<0.001"],    // успешность > 99.9%
        http_req_duration: ["p(95)<300"],
    }
};

function url(path) {
    return `${BASE}${path}`;
}

function rand(prefix) {
    return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export function setup() {
    const teamName = rand("team");

    const teamPayload = {
        team_name: teamName,
        members: [
            {user_id: "u1", username: "Alice", is_active: true},
            {user_id: "u2", username: "Bob", is_active: true},
            {user_id: "u3", username: "Cathy", is_active: true},
            {user_id: "u4", username: "Dan", is_active: false},
        ]
    };

    http.post(url("/api/v1/team/add"), JSON.stringify(teamPayload), {
        headers: {"Content-Type": "application/json"}
    });

    const prId = rand("pr");

    const prPayload = {
        pull_request_id: prId,
        pull_request_name: "Loadtest PR",
        author_id: "u1"
    };

    http.post(url("/api/v1/pullRequest/create"), JSON.stringify(prPayload), {
        headers: {"Content-Type": "application/json"}
    });

    return {
        teamName,
        prId
    };
}

export default function (data) {
    const r = Math.random();

    // 30% — team/get
    if (r < 0.30) {
        const res = http.get(url(`/api/v1/team/get?team_name=${data.teamName}`));
        check(res, {
            "team/get ok-ish": (r) => [200, 404].includes(r.status)
        });

        // 20% — users/getReview
    } else if (r < 0.50) {
        const res = http.get(url(`/api/v1/users/getReview?user_id=u2`));
        check(res, {
            "getReview ok-ish": (r) => [200, 404].includes(r.status)
        });

        // 25% — create PR
    } else if (r < 0.75) {
        const prId = rand("pr_new");
        const payload = {
            pull_request_id: prId,
            pull_request_name: "New load PR " + prId,
            author_id: "u1"
        };
        const res = http.post(url("/api/v1/pullRequest/create"), JSON.stringify(payload), {
            headers: {"Content-Type": "application/json"}
        });

        check(res, {
            "pr create ok-ish": (r) =>
                [200, 201, 400, 404, 409, 422].includes(r.status)
        });

        // 15% — merge PR
    } else if (r < 0.90) {
        const res = http.post(url("/api/v1/pullRequest/merge"), JSON.stringify({
            pull_request_id: data.prId
        }), {
            headers: {"Content-Type": "application/json"}
        });

        check(res, {
            "pr merge ok-ish": (r) =>
                [200, 400, 404, 409].includes(r.status)
        });

        // 10% — reassign reviewer
    } else {
        const res = http.post(url("/api/v1/pullRequest/reassign"), JSON.stringify({
            pull_request_id: data.prId,
            old_reviewer_id: "u2"
        }), {
            headers: {"Content-Type": "application/json"}
        });

        check(res, {
            "pr reassign ok-ish": (r) =>
                [200, 404, 409].includes(r.status)
        });
    }

    sleep(0.2);
}
