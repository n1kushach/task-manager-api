from fastapi import FastAPI

from app.api.routes import auth, tasks, users

# Error handling for all current routes, preferably write one global error handler for the whole project.
# Pagination.
# Read pytest doc and start writing tests.

app = FastAPI(title="Task Manager API")


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
