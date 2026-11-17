from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.core.database import Base
from app.main import app
from app.schemas.tasks import TaskCreate
from app.tests.test_tasks import TEST_TASK, create_task

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db) -> Generator[TestClient]:
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


TEST_USER = {"email": settings.test_username, "password": settings.test_password}


@pytest.fixture()
def registered_user(client: TestClient) -> dict[str, str]:
    res = client.post("/auth/register", json=TEST_USER)
    assert res.status_code in (200, 201)
    return TEST_USER


@pytest.fixture()
def auth_headers(client: TestClient, registered_user: dict[str, str]) -> dict[str, str]:
    res = client.post(
        "/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert res.status_code == 200
    body = res.json()
    print(res.status_code, res.json())
    return {
        "Authorization": f"{body['token_type'].capitalize()} {body['access_token']}"
    }


@pytest.fixture
def created_task(client: TestClient, auth_headers: dict[str, str]) -> TaskCreate:
    res = create_task(client, auth_headers, TEST_TASK)
    assert res.status_code in (200, 201), res.json()
    return res.json()
