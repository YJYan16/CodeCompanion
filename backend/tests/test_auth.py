def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_login_success(client):
    response = client.post("/api/login", json={"username": "2024001", "password": "123456"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["token"]
    assert data["user"]["username"] == "2024001"


def test_login_failure(client):
    response = client.post("/api/login", json={"username": "2024001", "password": "wrong"})
    assert response.status_code == 401


def test_me_requires_auth(client):
    response = client.get("/api/me")
    assert response.status_code == 401


def test_me_with_token(client, auth_headers):
    response = client.get("/api/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "admin"
