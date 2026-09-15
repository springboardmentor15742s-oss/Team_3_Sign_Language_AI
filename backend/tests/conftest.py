"""
Shared pytest fixtures. Every test run gets its own throwaway SQLite file
(never `backend/platform.db`) so tests are hermetic and repeatable.
"""
import os
import tempfile

import pytest


@pytest.fixture()
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)  # init_db() creates it fresh

    from database import db
    db.DB_PATH = path

    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as c:
        yield c

    if os.path.exists(path):
        os.remove(path)


def register_and_login(client, username, role="Learner"):
    client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{username}@example.com",
              "password": "Passw0rd!", "role": role},
    )
    r = client.post("/api/auth/login", json={"username": username, "password": "Passw0rd!"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def seed_attempts(username, gestures_with_accuracies):
    """gestures_with_accuracies: {"OPEN_PALM": [88, 90, 92], ...}"""
    import json
    from database import db

    user = db.get_user_by_username(username)
    for gesture, accuracies in gestures_with_accuracies.items():
        for acc in accuracies:
            db.log_gesture_attempt(user["id"], gesture, gesture, True, acc, acc, acc,
                                    json.dumps(["Great job!"]))
