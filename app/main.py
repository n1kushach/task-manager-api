from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.routes import auth, tasks, users

# Error handling for all current routes, preferably write one global error handler for the whole project.
# Pagination and filtering on GET /tasks.
# Read pytest doc and start writing tests.

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
