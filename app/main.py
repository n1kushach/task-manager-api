from fastapi import FastAPI

from app.api.routes import auth, tasks, users

# Read pytest doc and start writing tests.

app = FastAPI(title="Task Manager API")


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
