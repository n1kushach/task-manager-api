"""
Create (POST /tasks)

Minimal payload (title only) returns 201 (or whatever you use) and the defaults are applied: status == "todo", priority == "medium", description and due_date are None.
Full payload (all fields) is echoed back correctly.
owner_id equals the authenticated user’s id.
id, created_at, and updated_at are present in the response.
A client-supplied owner_id, id, or created_at in the body is ignored, so you can’t create a task for someone else.
Missing title returns 422.
Empty title ("") returns 422 (decide: only if you enforce min length).
Title over 200 characters: decide between 422 and truncation. SQLite won’t enforce String(200), so you need Pydantic max_length for this to be caught.
Wrong types (title as a number, due_date as "not-a-date") return 422.
Invalid status or priority value returns 422 (only if you validate against an enum).
A past due_date: decide whether it’s allowed.
No auth returns 401.
"""

"""
Read one (GET /tasks/{id})

Returns the task with all fields, matching what was created.
Nonexistent id returns 404.
Another user’s task returns 404 (already covered in test_auth.py; keep one here for CRUD completeness or skip the duplicate).
Non-integer id (/tasks/abc) returns 422.
No auth returns 401.
"""


"""
List (GET /tasks)

Empty list for a new user ([]).
Returns multiple tasks, all owned by the caller.
Doesn’t include other users’ tasks.
Ordering is as documented (by id, by created date, etc.). Pin down whatever your API promises.
If you support filters: ?status=done returns only matching tasks, an unknown status returns an empty list or 422 (decide), and a combined filter such as status plus priority returns the intersection.
If you support sorting or due_date filtering: ascending and descending order, tasks with None due dates (where do they go?), and a date range boundary on both ends.
If you support pagination: first page, last page, a page beyond the end (empty), limit=0 or a negative value (422), and a limit above your maximum.
No auth returns 401.
"""


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
