REGISTER_PAYLOAD = {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com",
    "password": "password123",
    "confirm_password": "password123",
}


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_success(client):
    resp = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    assert resp.status_code == 201
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "jane@example.com"
    assert data["user"]["role"] == "user"
    assert data["user"]["is_active"] is True


def test_register_duplicate_email_conflicts(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    assert resp.status_code == 409
    assert resp.json()["message"] == "Email already registered"


def test_register_password_mismatch(client):
    payload = {**REGISTER_PAYLOAD, "confirm_password": "different123"}
    resp = client.post("/api/v1/auth/register", json=payload)

    assert resp.status_code == 422


def test_login_success(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "jane@example.com", "password": "password123"},
    )

    assert resp.status_code == 200
    assert resp.json()["access_token"]
    assert resp.json()["user"]["email"] == "jane@example.com"


def test_login_wrong_password_unauthorized(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "jane@example.com", "password": "wrong-password"},
    )

    assert resp.status_code == 401


def test_me_requires_token(client):
    resp = client.get("/api/v1/auth/me")

    assert resp.status_code == 401


def test_me_with_token(client):
    token = client.post(
        "/api/v1/auth/register", json=REGISTER_PAYLOAD
    ).json()["access_token"]

    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert resp.json()["email"] == "jane@example.com"


def test_non_admin_cannot_update_role(client):
    token = client.post(
        "/api/v1/auth/register", json=REGISTER_PAYLOAD
    ).json()["access_token"]

    resp = client.patch(
        "/api/v1/users/1/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403