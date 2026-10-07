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


def unique_category_name(prefix: str = "Test Category") -> str:
    return f"{prefix} {uuid.uuid4().hex[:10]}"


def create_category(
    client: TestClient,
    admin_token: str,
    name: str | None = None,
    description: str = "Category created during automated testing",
) -> dict:
    if name is None:
        name = unique_category_name()

    response = client.post(
        "/api/categories",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": name,
            "description": description,
        },
    )

    assert response.status_code == 201

    return response.json()


def test_admin_can_create_category(client):
    admin_token = get_admin_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_category_name("Technical Test"),
        description="Technical support test category",
    )

    assert category["id"] > 0
    assert category["name"].startswith("Technical Test")
    assert category["description"] == "Technical support test category"
    assert category["is_active"] is True
    assert "created_at" in category
    assert "updated_at" in category


def test_all_authenticated_roles_can_list_categories(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)
    agent_token = get_agent_token(client)

    for token in (
        admin_token,
        customer_token,
        agent_token,
    ):
        response = client.get(
            "/api/categories",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 5

        for category in data:
            assert "id" in category
            assert "name" in category
            assert "description" in category
            assert "is_active" in category
            assert "created_at" in category
            assert "updated_at" in category


def test_admin_can_get_category_by_id(client):
    admin_token = get_admin_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_category_name("Get Category"),
        description="Get category test",
    )

    category_id = category["id"]

    response = client.get(
        f"/api/categories/{category_id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category_id
    assert data["name"] == category["name"]
    assert data["description"] == "Get category test"
    assert data["is_active"] is True


def test_customer_can_get_category_by_id(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_category_name("Customer Category"),
    )

    response = client.get(
        f"/api/categories/{category['id']}",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category["id"]
    assert data["name"] == category["name"]


def test_support_agent_can_get_category_by_id(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_category_name("Agent Category"),
    )

    response = client.get(
        f"/api/categories/{category['id']}",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category["id"]
    assert data["name"] == category["name"]


def test_admin_can_update_category(client):
    admin_token = get_admin_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_category_name("Original Category"),
        description="Original description",
    )

    category_id = category["id"]
    updated_name = unique_category_name("Updated Category")

    response = client.put(
        f"/api/categories/{category_id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": updated_name,
            "description": "Updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category_id
    assert data["name"] == updated_name
    assert data["description"] == "Updated description"
    assert data["is_active"] is True


def test_admin_can_update_only_description(client):
    admin_token = get_admin_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_category_name("Description Test"),
        description="Before update",
    )

    response = client.put(
        f"/api/categories/{category['id']}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "description": "After update",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category["id"]
    assert data["name"] == category["name"]
    assert data["description"] == "After update"


def test_duplicate_category_name_is_rejected(client):
    admin_token = get_admin_token(client)

    category_name = unique_category_name("Duplicate Category")

    first_response = client.post(
        "/api/categories",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": category_name,
            "description": "First category",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/categories",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": category_name,
            "description": "Second category",
        },
    )

    assert second_response.status_code == 409

    data = second_response.json()

    assert data["detail"] == "Category already exists"


def test_duplicate_category_name_is_rejected_when_updating(client):
    admin_token = get_admin_token(client)

    first_category = create_category(
        client,
        admin_token,
        name=unique_category_name("First Category"),
    )

    second_category = create_category(
        client,
        admin_token,
        name=unique_category_name("Second Category"),
    )

    response = client.put(
        f"/api/categories/{second_category['id']}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": first_category["name"],
        },
    )

    assert response.status_code == 409

    data = response.json()

    assert data["detail"] == "Category already exists"


def test_admin_can_deactivate_category(client):
    admin_token = get_admin_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_category_name("Deactivate Category"),
    )

    response = client.patch(
        f"/api/categories/{category['id']}/deactivate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category["id"]
    assert data["is_active"] is False


def test_admin_can_activate_category(client):
    admin_token = get_admin_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_category_name("Activate Category"),
    )

    deactivate_response = client.patch(
        f"/api/categories/{category['id']}/deactivate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False

    activate_response = client.patch(
        f"/api/categories/{category['id']}/activate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert activate_response.status_code == 200

    data = activate_response.json()

    assert data["id"] == category["id"]
    assert data["is_active"] is True


def test_customer_cannot_create_category(client):
    customer_token = get_customer_token(client)

    response = client.post(
        "/api/categories",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "name": unique_category_name("Customer Create"),
            "description": "Should fail",
        },
    )

    assert response.status_code == 403


def test_support_agent_cannot_create_category(client):
    agent_token = get_agent_token(client)

    response = client.post(
        "/api/categories",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "name": unique_category_name("Agent Create"),
            "description": "Should fail",
        },
    )

    assert response.status_code == 403


def test_customer_cannot_update_category(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_category_name("Customer Update"),
    )

    response = client.put(
        f"/api/categories/{category['id']}",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "name": unique_category_name("Unauthorized Update"),
        },
    )

    assert response.status_code == 403


def test_support_agent_cannot_update_category(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_category_name("Agent Update"),
    )

    response = client.put(
        f"/api/categories/{category['id']}",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "name": unique_category_name("Unauthorized Update"),
        },
    )

    assert response.status_code == 403


def test_customer_cannot_deactivate_category(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_category_name("Customer Deactivate"),
    )

    response = client.patch(
        f"/api/categories/{category['id']}/deactivate",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert response.status_code == 403


def test_support_agent_cannot_deactivate_category(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_category_name("Agent Deactivate"),
    )

    response = client.patch(
        f"/api/categories/{category['id']}/deactivate",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_list_categories(client):
    response = client.get("/api/categories")

    assert response.status_code in {401, 403}


def test_get_nonexistent_category_returns_404(client):
    admin_token = get_admin_token(client)

    response = client.get(
        "/api/categories/999999999",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Category not found"


def test_update_nonexistent_category_returns_404(client):
    admin_token = get_admin_token(client)

    response = client.put(
        "/api/categories/999999999",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": unique_category_name("Missing Category"),
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Category not found"


def test_activate_nonexistent_category_returns_404(client):
    admin_token = get_admin_token(client)

    response = client.patch(
        "/api/categories/999999999/activate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 404


def test_deactivate_nonexistent_category_returns_404(client):
    admin_token = get_admin_token(client)

    response = client.patch(
        "/api/categories/999999999/deactivate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 404