"""
Auth tests for the task manager API.

Expects these fixtures in app/tests/conftest.py:
  - client:           fastapi.testclient.TestClient wired to the test DB
  - registered_user:  UserCredentials dict of a user already registered
  - auth_headers:     {"Authorization": "Bearer <token>"} for registered_user

Adjust endpoint paths, status codes, and the config import to match your app.
"""

import time
from typing import TypedDict

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


class UserCredentials(TypedDict):
    email: str
    password: str


OTHER_USER: UserCredentials = {"email": "testing@example.com", "password": "12341234"}


# ---------- HELPERS ----------


def login(client: TestClient, username: str, password: str):
    return client.post("/auth/login", data={"username": username, "password": password})


def register(client: TestClient, username: str, password: str):
    print(username, password)
    return client.post("/auth/register", json={"email": username, "password": password})


def make_token(
    sub: str = "1", expires_in: int = 600, secret: str = settings.secret_key
) -> str:
    payload = {"sub": sub, "exp": int(time.time()) + expires_in}
    return jwt.encode(payload, secret, algorithm=settings.algorithm)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------- REGISTRATION ----------


def test_register_success(client: TestClient):
    res = client.post("/auth/register", json=OTHER_USER)
    assert res.status_code in (200, 201)
    body = res.json()
    print(f"Body - {body}")
    assert body["email"] == OTHER_USER["email"]
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email(client: TestClient, registered_user: UserCredentials):
    res = client.post("/auth/register", json=registered_user)
    assert res.status_code in (400, 409)  # match your API


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"email": "a@gmail.com"},
        {"password": "12341234"},
        {"email": "not-an-email", "password": "12341234"},
    ],
)
def test_register_validation_errors(client: TestClient, payload):
    assert client.post("/auth/register", json=payload).status_code == 422


# ---------- LOGIN ----------


def test_login_success(client: TestClient, registered_user: UserCredentials):
    res = login(client, registered_user["email"], registered_user["password"])
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]


def test_login_token_contents(client: TestClient, registered_user: UserCredentials):
    res = login(client, registered_user["email"], registered_user["password"])
    payload = jwt.decode(
        res.json()["access_token"], settings.secret_key, algorithms=[settings.algorithm]
    )
    assert "sub" in payload  # user id
    assert payload["exp"] > time.time()  # expires in the future


def test_login_wrong_password(client: TestClient, registered_user: UserCredentials):
    res = login(client, registered_user["email"], "wrong-password")
    assert res.status_code == 401  # or 400/403, match your API
    assert "access_token" not in res.json()


def test_login_unknown_user(client: TestClient):
    res = login(client, "nobody@gmail.com", "12341234")
    assert res.status_code == 401
    assert "access_token" not in res.json()


def test_login_wrong_password_and_unknown_user_errors_match(
    client: TestClient, registered_user: UserCredentials
):
    # Identical responses so attackers can't tell which emails are registered
    a = login(client, registered_user["email"], "wrong")
    b = login(client, "nobody@gmail.com", "wrong")
    assert a.status_code == b.status_code
    assert a.json() == b.json()


@pytest.mark.parametrize(
    "payload",
    [{}, {"email": "test@gmail.com"}, {"password": "12341234"}],
)
def test_login_missing_fields(client: TestClient, payload):
    assert client.post("/auth/login", data=payload).status_code == 422


def test_login_invalid_email_format(client: TestClient):
    # Returns 422 if schema uses EmailStr
    res = client.post(
        "/auth/login", data={"email": "not-an-email", "password": "12341234"}
    )
    assert res.status_code == 422


def test_login_rejects_form_body(client: TestClient, registered_user: UserCredentials):
    # JSON-only login shouldn't accept form data
    res = client.post(
        "/auth/login",
        data={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert res.status_code == 422


# ---------- PROTECTED ROUTES: TOKEN VALIDATION ----------


def test_protected_route_without_token(client: TestClient):
    assert client.get("/tasks").status_code == 401


def test_protected_route_with_valid_token(
    client: TestClient, auth_headers: dict[str, str]
):
    assert client.get("/tasks", headers=auth_headers).status_code == 200


def test_protected_route_with_garbage_token(client: TestClient):
    res = client.get("/tasks", headers=bearer("not.a.token"))
    assert res.status_code == 401


def test_protected_route_with_wrong_scheme(
    client: TestClient, auth_headers: dict[str, str]
):
    token = auth_headers["Authorization"].split(" ", 1)[1]
    res = client.get("/tasks", headers={"Authorization": f"Basic {token}"})
    assert res.status_code == 401


def test_protected_route_with_expired_token(client: TestClient):
    res = client.get("/tasks", headers=bearer(make_token(expires_in=-60)))
    assert res.status_code == 401


def test_protected_route_with_wrong_signature(client: TestClient):
    res = client.get("/tasks", headers=bearer(make_token(secret="wrong-secret")))
    assert res.status_code == 401


def test_protected_route_with_token_missing_sub(client: TestClient):
    token = jwt.encode(
        {"exp": int(time.time()) + 600},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    assert client.get("/tasks", headers=bearer(token)).status_code == 401


def test_token_for_nonexistent_user(
    client: TestClient, registered_user: UserCredentials
):
    # Valid signature, but the user id doesn't exist
    res = client.get("/tasks", headers=bearer(make_token(sub="99999")))
    assert res.status_code == 401


def test_alg_none_token_rejected(client: TestClient):
    # Classic JWT attack: unsigned token claiming alg "none"
    token = jwt.encode(
        {"sub": "1", "exp": int(time.time()) + 600}, key="", algorithm="none"
    )
    assert client.get("/tasks", headers=bearer(token)).status_code == 401


# # ---------- authorization: user isolation ----------


def test_user_cannot_access_another_users_task(
    client: TestClient, auth_headers: dict[str, str]
):
    task_id = client.post(
        "/tasks", json={"title": "mine"}, headers=auth_headers
    ).json()["task"]["id"]

    res = client.post("/auth/register", json=OTHER_USER)
    assert res.status_code in (200, 201), res.json()

    other_token = login(client, OTHER_USER["email"], OTHER_USER["password"]).json()[
        "access_token"
    ]
    other_headers = bearer(other_token)
    print(other_headers)

    r = client.get(f"/tasks/{task_id}", headers=other_headers)
    assert r.status_code in (403, 404), f"GET leaked: {r.status_code} {r.json()}"

    r = client.post(f"/tasks/{task_id}", json={"status": "done"}, headers=other_headers)
    assert r.status_code in (403, 404), f"PATCH leaked: {r.status_code} {r.json()}"

    r = client.delete(f"/tasks/{task_id}", headers=other_headers)
    assert r.status_code in (403, 404), f"DELETE leaked: {r.status_code} {r.json()}"

    # The owner's task is untouched
    res = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] != "done"


def test_task_list_only_shows_own_tasks(
    client: TestClient, auth_headers: dict[str, str]
):
    client.post("/tasks", json={"title": "mine"}, headers=auth_headers)

    client.post("/auth/register", json=OTHER_USER)
    other_token = login(client, OTHER_USER["email"], OTHER_USER["password"]).json()[
        "access_token"
    ]

    res = client.get("/tasks", headers=bearer(other_token))
    assert res.status_code == 200
    assert res.json()["tasks"] == []
