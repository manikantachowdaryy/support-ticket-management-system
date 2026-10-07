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


def test_customer_can_add_comment(client):
    token = get_customer_token(client)

    response = client.post(
        "/api/tickets/1/comments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "comment": "This is a test comment from the customer.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["ticket_id"] == 1
    assert data["comment"] == "This is a test comment from the customer."
    assert data["user_id"] == 1


def test_agent_can_add_comment(client):
    token = get_agent_token(client)

    response = client.post(
        "/api/tickets/1/comments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "comment": "This is a test comment from the support agent.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["ticket_id"] == 1
    assert data["comment"] == "This is a test comment from the support agent."
    assert data["user_id"] == 3


def test_list_ticket_comments(client):
    token = get_customer_token(client)

    response = client.get(
        "/api/tickets/1/comments",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_user_can_update_own_comment(client):
    token = get_customer_token(client)

    create_response = client.post(
        "/api/tickets/1/comments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "comment": "Comment that will be updated.",
        },
    )

    assert create_response.status_code == 201

    comment_id = create_response.json()["id"]

    response = client.put(
        f"/api/tickets/comments/{comment_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "comment": "Updated customer comment.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == comment_id
    assert data["comment"] == "Updated customer comment."
    assert data["user_id"] == 1
    assert data["ticket_id"] == 1


def test_user_cannot_update_another_users_comment(client):
    customer_token = get_customer_token(client)

    create_response = client.post(
        "/api/tickets/1/comments",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "comment": "Customer private comment.",
        },
    )

    assert create_response.status_code == 201

    comment_id = create_response.json()["id"]

    agent_token = get_agent_token(client)

    response = client.put(
        f"/api/tickets/comments/{comment_id}",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "comment": "Agent trying to modify customer comment.",
        },
    )

    assert response.status_code == 403


def test_user_can_delete_own_comment(client):
    token = get_customer_token(client)

    create_response = client.post(
        "/api/tickets/1/comments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "comment": "Comment that will be deleted.",
        },
    )

    assert create_response.status_code == 201

    comment_id = create_response.json()["id"]

    response = client.delete(
        f"/api/tickets/comments/{comment_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 204


def test_user_cannot_delete_another_users_comment(client):
    customer_token = get_customer_token(client)

    create_response = client.post(
        "/api/tickets/1/comments",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "comment": "Customer comment for delete authorization test.",
        },
    )

    assert create_response.status_code == 201

    comment_id = create_response.json()["id"]

    agent_token = get_agent_token(client)

    response = client.delete(
        f"/api/tickets/comments/{comment_id}",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert response.status_code == 403


def test_admin_can_moderate_comment(client):
    customer_token = get_customer_token(client)

    create_response = client.post(
        "/api/tickets/1/comments",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "comment": "Comment for admin moderation test.",
        },
    )

    assert create_response.status_code == 201

    comment_id = create_response.json()["id"]

    admin_token = get_admin_token(client)

    response = client.delete(
        f"/api/tickets/comments/{comment_id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 204


def test_comment_requires_authentication(client):
    response = client.post(
        "/api/tickets/1/comments",
        json={
            "comment": "Unauthenticated comment.",
        },
    )

    assert response.status_code in {401, 403}