import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.services.dataset_service import get_dataset_summary, find_asl_dataset_dir

# In-memory SQLite DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        try:
            os.remove("./test.db")
        except OSError:
            pass

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_user_registration_and_login():
    # 1. Register a new user
    register_payload = {
        "email": "testlearner@example.com",
        "username": "testlearner",
        "password": "Password123!",
        "full_name": "Test Learner",
        "role_name": "learner"
    }
    reg_response = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_response.status_code == 201
    user_data = reg_response.json()
    assert user_data["email"] == "testlearner@example.com"
    assert user_data["role"]["name"] == "learner"

    # 2. Login with valid credentials
    login_payload = {
        "email": "testlearner@example.com",
        "password": "Password123!"
    }
    login_response = client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # 3. Access protected route (/auth/me)
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "testlearner"

    # 4. Access protected profile route (/learner-profiles/me)
    profile_response = client.get("/api/v1/learner-profiles/me", headers=headers)
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["learning_level"] == "beginner"


def test_profile_update():
    # Register and login
    client.post("/api/v1/auth/register", json={
        "email": "updateuser@example.com",
        "username": "updateuser",
        "password": "Password123!",
        "full_name": "Update User"
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": "updateuser@example.com",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update profile
    update_payload = {
        "full_name": "Updated User Name",
        "learning_level": "intermediate",
        "preferred_language": "ASL",
        "learning_goals": "Master sign alphabet completely"
    }
    update_res = client.put("/api/v1/learner-profiles/me", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["full_name"] == "Updated User Name"
    assert updated_data["learning_level"] == "intermediate"


def test_dataset_summary_api():
    response = client.get("/api/v1/dataset/summary")
    assert response.status_code == 200
    data = response.json()
    assert "dataset_status" in data
    assert "available_classes" in data
    assert "number_of_classes" in data
    assert "total_train_images" in data
    assert "total_test_images" in data


def test_dataset_service_detection():
    summary = get_dataset_summary()
    assert summary is not None
    assert summary["dataset_status"] in ["ready", "incomplete", "not_found"]
