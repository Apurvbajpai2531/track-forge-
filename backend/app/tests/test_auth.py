from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_and_login():
    client.post("/api/auth/register", json={
        "username": "tester1", "email": "tester1@example.com", "password": "pass1234"
    })
    resp = client.post("/api/auth/login", json={"username": "tester1", "password": "pass1234"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password():
    resp = client.post("/api/auth/login", json={"username": "tester1", "password": "wrong"})
    assert resp.status_code == 401
