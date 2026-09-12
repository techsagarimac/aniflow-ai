from tests.conftest import auth_header


def test_login_success(client):
    res = client.post("/api/auth/login", json={"email": "manager@aniflow.ai", "password": "demo1234"})
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"]
    assert body["user"]["role"] == "production_manager"


def test_login_invalid(client):
    res = client.post("/api/auth/login", json={"email": "manager@aniflow.ai", "password": "wrongpass"})
    assert res.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401
    res = client.get("/api/auth/me", headers=auth_header(client))
    assert res.status_code == 200
    assert res.json()["email"] == "manager@aniflow.ai"
