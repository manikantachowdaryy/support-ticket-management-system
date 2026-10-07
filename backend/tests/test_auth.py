import uuid
def test_register_customer(client):
    email = f"pytest_customer_{uuid.uuid4().hex[:8]}@test.com"

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Pytest Customer",
            "email": email,
            "password": "Test@12345",
        },
    )

    assert response.status_code == 200



def test_login_success(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@support.com",
            "password": "Admin@123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@support.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid email or password"


def test_login_unknown_user(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "doesnotexist@test.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid email or password"


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")

    assert response.status_code in {401, 403}


def test_me_authenticated(client):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@support.com",
            "password": "Admin@123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "admin@support.com"
    assert data["role"] == "ADMIN"
    assert data["is_active"] is True