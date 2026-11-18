import pytest
from fastapi.testclient import TestClient

TEST_TASK = {
    "title": "Test task title",
    "description": "Test task description",
    "status": "todo",
    "priority": "medium",
    "due_date": "2026-11-18",
}


# Helpers
def create_task(client: TestClient, auth_headers: dict[str, str], payload):
    return client.post("/tasks", headers=auth_headers, json=payload)


def get_task_by_id(client: TestClient, auth_headers: dict[str, str], payload):
    return client.get(f"/tasks/{payload}", headers=auth_headers)


def get_tasks(client: TestClient, auth_headers: dict[str, str]):
    return client.get("/tasks", headers=auth_headers)


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="missing-title"),
        pytest.param({"title": ""}, id="empty-title"),
        pytest.param({"title": 123}, id="title-not-string"),
        pytest.param({"title": "a" * 201}, id="title-too-long"),
        pytest.param({"title": "x", "due_date": "not-a-date"}, id="due-date-garbage"),
        pytest.param(
            {"title": "x", "due_date": "2026-13-45"}, id="due-date-impossible"
        ),
        pytest.param({"title": "x", "status": "bogus"}, id="status-invalid"),
    ],
)
# Checking validation errors
def test_create_task_invalid_payload(
    client: TestClient, auth_headers: dict[str, str], payload
):
    res = create_task(client, auth_headers, payload)
    assert res.status_code == 422, res.json()


@pytest.mark.parametrize("payload", [{"title": "Test title"}, TEST_TASK])
# Checking task creation with correct fields
def test_create_task(client: TestClient, auth_headers: dict[str, str], payload):
    res = create_task(client, auth_headers, payload)
    body = res.json()
    id = body["task"]["id"]
    created_at = body["task"]["created_at"]
    updated_at = body["task"]["updated_at"]
    assert res.status_code in (201, 200), (id, created_at, updated_at) in body


@pytest.mark.parametrize("payload", [{"title": "Minimal payload"}])
def test_create_task_minimal_payload(
    client: TestClient, auth_headers: dict[str, str], payload
):
    res = create_task(client, auth_headers, payload)
    body = res.json()
    assert body["task"]["status"] == "todo", (
        body["task"]["priority"] == "medium" in body
    )


@pytest.mark.parametrize("payload", [TEST_TASK])
def test_create_task_full_payload(
    client: TestClient, auth_headers: dict[str, str], payload
):
    res = create_task(client, auth_headers, payload)
    body = res.json()
    task = body["task"]
    required = {
        "title",
        "description",
        "status",
        "priority",
        "due_date",
        "id",
        "owner_id",
        "created_at",
        "updated_at",
    }
    assert required <= task.keys(), f"Missing: {required - task.keys()}"


@pytest.mark.parametrize("payload", [{**TEST_TASK, "owner_id": 9999}])
def test_cant_create_task_for_other(
    client: TestClient,
    auth_headers: dict[str, str],
    payload,
):
    me = client.get("/users/me", headers=auth_headers)
    assert me.status_code == 200, me.json()
    user_id = me.json()["id"]

    assert payload["owner_id"] != user_id

    res = create_task(client, auth_headers, payload)
    assert res.status_code == 422, res.json()


def test_get_single_task_with_all_fields(
    client: TestClient, auth_headers: dict[str, str], created_task
):
    res = get_task_by_id(client, auth_headers, created_task["task"]["id"])
    task = res.json()
    required = {
        "title",
        "description",
        "status",
        "priority",
        "due_date",
        "id",
        "owner_id",
        "created_at",
        "updated_at",
    }
    assert required <= task.keys(), f"Missing: {required - task.keys()}"


def test_get_single_task_without_id(client: TestClient, auth_headers: dict[str, str]):
    res = get_task_by_id(client, auth_headers, payload=None)
    assert res.status_code == 422


def test_get_single_task_with_nonexistent_id(
    client: TestClient, auth_headers: dict[str, str], created_task
):
    missing_id = created_task["task"]["id"] + 1
    res = client.get(f"/tasks/{missing_id}", headers=auth_headers)
    assert res.status_code == 404, res.json()


def test_get_single_task_of_another_user(
    client: TestClient, auth_headers, other_user_headers
):
    other_user_created = create_task(
        client, other_user_headers, {"title": "Other user title"}
    )
    task_id = other_user_created.json()["task"]["id"]
    assert get_task_by_id(client, other_user_headers, task_id).status_code == 200
    res = get_task_by_id(client, auth_headers, task_id)
    assert res.status_code == 404, res.text


def test_get_single_task_with_no_auth(client: TestClient, created_task):
    created_task_id = created_task["task"]["id"]
    res = get_task_by_id(client, {}, created_task_id)
    assert res.status_code == 401, res.json()


def test_get_single_task_with_non_integer_id(client: TestClient, auth_headers):
    res = get_task_by_id(client, auth_headers, "abc")
    assert res.status_code == 422, res.json()


"""
List (GET /tasks)

If you support filters: ?status=done returns only matching tasks, an unknown status returns an empty list or 422 (decide), and a combined filter such as status plus priority returns the intersection.
If you support sorting or due_date filtering: ascending and descending order, tasks with None due dates (where do they go?), and a date range boundary on both ends.
If you support pagination: first page, last page, a page beyond the end (empty), limit=0 or a negative value (422), and a limit above your maximum.
No auth returns 401.
"""


def test_get_tasks_new_user(client: TestClient, auth_headers):
    res = get_tasks(client, auth_headers)
    body = res.json()
    assert len(body["tasks"]) == 0
    assert body["total"] == 0


def test_get_tasks_returns_only_own_tasks(
    client: TestClient, auth_headers, other_user_headers, created_tasks
):
    # Another user's task must not show up in my list
    other = create_task(client, other_user_headers, {"title": "Not mine"})
    assert other.status_code in (200, 201), other.text

    res = client.get("/tasks", headers=auth_headers)
    assert res.status_code == 200, res.text
    body = res.json()

    assert body["total"] == len(created_tasks), body
    assert len(body["tasks"]) == len(created_tasks), body

    # All returned tasks belong to the caller
    user_id = created_tasks[0]["owner_id"]
    assert all(t["owner_id"] == user_id for t in body["tasks"]), body

    # Exactly my tasks came back, and not the other user's
    assert {t["id"] for t in body["tasks"]} == {t["id"] for t in created_tasks}


def test_get_tasks_ordering(client: TestClient, auth_headers):
    created_ids = []
    for i in range(3):
        res = create_task(client, auth_headers, {"title": f"Task-{i}"})
        body = res.json()
        created_ids.append(body["task"]["id"])
    res = get_tasks(client, auth_headers)
    body = res.json()
    returned_ids = [t["id"] for t in body["tasks"]]
    assert returned_ids == list(reversed(created_ids)), returned_ids


"""
Update (POST /tasks/{id})

Update one field (status to "done"): the response shows the new value, and other fields are unchanged.
Update several fields at once.
Partial update leaves omitted fields untouched (this catches code that overwrites with None).
Explicitly set description or due_date to null: decide whether that clears it.
Empty body {}: decide between 200 no-op and 422.
updated_at changes after an update and created_at doesn’t. SQLite’s now() has one-second resolution, so either wait a bit or compare with >= rather than >.
A GET after the update returns the persisted values.
Invalid values (bad status, empty title, wrong types) return 422, and the task is unchanged afterwards.
Attempt to change owner_id or id through the body is ignored.
Nonexistent id returns 404.
Another user’s task returns 404 and the owner’s task is unchanged (covered, but worth a positive control: the owner can update it).
No auth returns 401.
"""


"""
Delete (DELETE /tasks/{id})

Returns your documented success code (204 or 200), and a following GET returns 404.
The task disappears from the list.
Deleting twice: the second call returns 404.
Nonexistent id returns 404.
Another user’s task returns 404 and the task still exists for the owner.
Deleting one task doesn’t affect the owner’s other tasks.
No auth returns 401.
"""


"""
Cross-cutting

Full lifecycle in one test: create, read, update, list, delete, read (404). This catches wiring errors the unit-style tests miss.
Two users creating tasks with the same title don’t interfere.
Response shape: the set of keys in the response matches your schema, with no leaked internals.
Unicode and long text in title and description round-trip unchanged.
HTML or SQL-looking strings are stored and returned as plain text.

Suggested order
Start with create, read, and delete happy paths. They need the least decision-making. Then add the 404 and 401 cases, then validation, then update, then filters and pagination. Use pytest.mark.parametrize for the validation and 401 cases, since they’re the same test with different inputs.

When you’ve written some of these, paste them (or any failures) and I can review them.
"""
