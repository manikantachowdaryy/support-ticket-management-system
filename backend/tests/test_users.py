import uuid

from fastapi.testclient import TestClient


ADMIN_EMAIL = "admin@support.com"
ADMIN_PASSWORD = "Admin@123"

CUSTOMER_EMAIL = "customer@test.com"
CUSTOMER_PASSWORD = "Customer@123"

AGENT_EMAIL = "agent@support.com"
AGENT_PASSWORD = "Agent@123"


def get_token(
    client: TestClient,
    email: str,
    password: str,
) -> str:
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def get_admin_token(client: TestClient) -> str:
    return get_token(
        client,
        ADMIN_EMAIL,
        ADMIN_PASSWORD,
    )


def get_customer_token(client: TestClient) -> str:
    return get_token(
        client,
        CUSTOMER_EMAIL,
        CUSTOMER_PASSWORD,
    )


def get_agent_token(client: TestClient) -> str:
    return get_token(
        client,
        AGENT_EMAIL,
        AGENT_PASSWORD,
    )


def unique_email(prefix: str = "pytest_user") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}@test.com"


def create_test_user(
    client: TestClient,
    admin_token: str,
    role: str = "CUSTOMER",
    name: str = "Pytest Test User",
    email: str | None = None,
) -> dict:
    if email is None:
        email = unique_email()

    response = client.post(
        "/api/users",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": name,
            "email": email,
            "password": "TestUser@123",
            "role": role,
        },
    )

    assert response.status_code == 201

    return response.json()


def test_admin_can_create_customer(client):
    admin_token = get_admin_token(client)

    user = create_test_user(
        client,
        admin_token,
        role="CUSTOMER",
        name="Created Customer",
    )

    assert user["id"] > 0
    assert user["name"] == "Created Customer"
    assert user["email"].endswith("@test.com")
    assert user["role"] == "CUSTOMER"
    assert user["is_active"] is True
    assert "created_at" in user
    assert "updated_at" in user


def test_admin_can_create_support_agent(client):
    admin_token = get_admin_token(client)

    user = create_test_user(
        client,
        admin_token,
        role="SUPPORT_AGENT",
        name="Created Support Agent",
    )

    assert user["id"] > 0
    assert user["role"] == "SUPPORT_AGENT"
    assert user["is_active"] is True


def test_admin_can_list_users(client):
    admin_token = get_admin_token(client)

    response = client.get(
        "/api/users",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 3

    for user in data:
        assert "id" in user
        assert "name" in user
        assert "email" in user
        assert "role" in user
        assert "is_active" in user
        assert "created_at" in user
        assert "updated_at" in user


def test_admin_can_get_user_by_id(client):
    admin_token = get_admin_token(client)

    user = create_test_user(
        client,
        admin_token,
        name="Get User Test",
    )

    user_id = user["id"]

    response = client.get(
        f"/api/users/{user_id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_id
    assert data["name"] == "Get User Test"
    assert data["email"] == user["email"]
    assert data["role"] == "CUSTOMER"
    assert data["is_active"] is True


def test_admin_can_update_user(client):
    admin_token = get_admin_token(client)

    user = create_test_user(
        client,
        admin_token,
        name="Original User Name",
    )

    user_id = user["id"]

    new_email = unique_email("updated_user")

    response = client.put(
        f"/api/users/{user_id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "Updated User Name",
            "email": new_email,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_id
    assert data["name"] == "Updated User Name"
    assert data["email"] == new_email
    assert data["role"] == "CUSTOMER"
    assert data["is_active"] is True


def test_admin_can_change_user_role(client):
    admin_token = get_admin_token(client)

    user = create_test_user(
        client,
        admin_token,
        role="CUSTOMER",
        name="Role Change Test",
    )

    user_id = user["id"]

    response = client.patch(
        f"/api/users/{user_id}/role",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "role": "SUPPORT_AGENT",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_id
    assert data["role"] == "SUPPORT_AGENT"


def test_admin_can_deactivate_user(client):
    admin_token = get_admin_token(client)

    user = create_test_user(
        client,
        admin_token,
        name="Deactivate Test User",
    )

    user_id = user["id"]

    response = client.patch(
        f"/api/users/{user_id}/deactivate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_id
    assert data["is_active"] is False


def test_admin_can_activate_user(client):
    admin_token = get_admin_token(client)

    user = create_test_user(
        client,
        admin_token,
        name="Activate Test User",
    )

    user_id = user["id"]

    deactivate_response = client.patch(
        f"/api/users/{user_id}/deactivate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False

    activate_response = client.patch(
        f"/api/users/{user_id}/activate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert activate_response.status_code == 200

    data = activate_response.json()

    assert data["id"] == user_id
    assert data["is_active"] is True


def test_deactivated_user_cannot_login(client):
    admin_token = get_admin_token(client)

    email = unique_email("inactive_user")

    user = create_test_user(
        client,
        admin_token,
        role="CUSTOMER",
        name="Inactive Login Test",
        email=email,
    )

    user_id = user["id"]

    deactivate_response = client.patch(
        f"/api/users/{user_id}/deactivate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert deactivate_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "TestUser@123",
        },
    )

    assert login_response.status_code == 401


def test_duplicate_email_is_rejected(client):
    admin_token = get_admin_token(client)

    email = unique_email("duplicate_test")

    first_response = client.post(
        "/api/users",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "First Duplicate User",
            "email": email,
            "password": "TestUser@123",
            "role": "CUSTOMER",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/users",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "Second Duplicate User",
            "email": email,
            "password": "TestUser@123",
            "role": "CUSTOMER",
        },
    )

    assert second_response.status_code == 409

    data = second_response.json()

    assert data["detail"] == "Email already registered"


def test_invalid_role_is_rejected_when_creating_user(client):
    admin_token = get_admin_token(client)

    response = client.post(
        "/api/users",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "Invalid Role User",
            "email": unique_email("invalid_role"),
            "password": "TestUser@123",
            "role": "MANAGER",
        },
    )

    assert response.status_code == 409

    data = response.json()

    assert data["detail"] == "Invalid role"


def test_invalid_role_is_rejected_when_changing_role(client):
    admin_token = get_admin_token(client)

    user = create_test_user(
        client,
        admin_token,
        role="CUSTOMER",
        name="Invalid Role Change",
    )

    user_id = user["id"]

    response = client.patch(
        f"/api/users/{user_id}/role",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "role": "MANAGER",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Invalid role"


def test_customer_cannot_manage_users(client):
    customer_token = get_customer_token(client)

    response = client.get(
        "/api/users",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert response.status_code == 403


def test_support_agent_cannot_manage_users(client):
    agent_token = get_agent_token(client)

    response = client.get(
        "/api/users",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_manage_users(client):
    response = client.get(
        "/api/users",
    )

    assert response.status_code in {401, 403}


def test_get_nonexistent_user_returns_404(client):
    admin_token = get_admin_token(client)

    response = client.get(
        "/api/users/999999999",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "User not found"


def test_update_nonexistent_user_returns_404(client):
    admin_token = get_admin_token(client)

    response = client.put(
        "/api/users/999999999",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "Updated Nonexistent",
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "User not found"


def test_deactivate_nonexistent_user_returns_404(client):
    admin_token = get_admin_token(client)

    response = client.patch(
        "/api/users/999999999/deactivate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 404


def test_activate_nonexistent_user_returns_404(client):
    admin_token = get_admin_token(client)

    response = client.patch(
        "/api/users/999999999/activate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 404


def test_change_role_nonexistent_user_returns_404(client):
    admin_token = get_admin_token(client)

    response = client.patch(
        "/api/users/999999999/role",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "role": "CUSTOMER",
        },
    )

    assert response.status_code == 404