from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.routes import auth, tasks, users

# services/task_service.py: functions like create_task, get_task, list_tasks, update_task, delete_task. Every query filters by owner_id.
# routes/tasks.py: POST /tasks, GET /tasks, GET /tasks/{id}, PATCH /tasks/{id}, DELETE /tasks/{id}, all using Depends(get_current_user).
# Error handling for all current routes, preferably write one global error handler for the whole project.
# Pagination and filtering on GET /tasks.
# Tests with pytest.

app = FastAPI(title="Task Manager API")


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)


@app.get("/health/db")
async def check_database(db: Session = Depends(get_db)):
    print("1. Endpoint reached")

    try:
        print("2. Executing query")

        result = db.execute(text("SELECT 1"))

        print("3. Query executed")

        return {
            "status": "success",
            "database": "connected",
            "result": result.scalar(),
        }

    except Exception as e:
        print(f"Database error: {e}")

        raise HTTPException(
            status_code=503,
            detail=str(e),
        )
