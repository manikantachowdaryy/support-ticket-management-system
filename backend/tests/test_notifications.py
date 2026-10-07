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


def create_customer_ticket(
    client: TestClient,
    customer_token: str,
    title: str,
) -> dict:
    response = client.post(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "title": title,
            "description": (
                "This ticket is created for notification testing."
            ),
            "category_id": 1,
            "priority": "MEDIUM",
        },
    )

    assert response.status_code == 201

    return response.json()


def find_notification(
    notifications: list[dict],
    ticket_id: int,
    notification_type: str,
) -> dict | None:
    for notification in notifications:
        if (
            notification.get("ticket_id") == ticket_id
            and notification.get("notification_type")
            == notification_type
        ):
            return notification

    return None


def test_admin_receives_ticket_created_notification(client):
    customer_token = get_customer_token(client)
    admin_token = get_admin_token(client)

    ticket = create_customer_ticket(
        client,
        customer_token,
        "Notification ticket created test",
    )

    ticket_id = ticket["id"]

    response = client.get(
        "/api/notifications",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    notifications = response.json()

    assert isinstance(notifications, list)

    notification = find_notification(
        notifications,
        ticket_id,
        "TICKET_CREATED",
    )

    assert notification is not None
    assert notification["ticket_id"] == ticket_id
    assert notification["notification_type"] == "TICKET_CREATED"
    assert notification["is_read"] is False


def test_agent_receives_ticket_assigned_notification(client):
    customer_token = get_customer_token(client)
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)

    ticket = create_customer_ticket(
        client,
        customer_token,
        "Notification assignment test",
    )

    ticket_id = ticket["id"]

    assign_response = client.patch(
        f"/api/tickets/{ticket_id}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "agent_id": 3,
        },
    )

    assert assign_response.status_code == 200

    response = client.get(
        "/api/notifications",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert response.status_code == 200

    notifications = response.json()

    notification = find_notification(
        notifications,
        ticket_id,
        "TICKET_ASSIGNED",
    )

    assert notification is not None
    assert notification["ticket_id"] == ticket_id
    assert notification["notification_type"] == "TICKET_ASSIGNED"
    assert notification["is_read"] is False


def test_agent_receives_new_comment_notification(client):
    customer_token = get_customer_token(client)
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)

    ticket = create_customer_ticket(
        client,
        customer_token,
        "Notification comment test",
    )

    ticket_id = ticket["id"]

    assign_response = client.patch(
        f"/api/tickets/{ticket_id}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "agent_id": 3,
        },
    )

    assert assign_response.status_code == 200

    comment_response = client.post(
        f"/api/tickets/{ticket_id}/comments",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "comment": "Testing notification after customer comment.",
        },
    )

    assert comment_response.status_code == 201

    response = client.get(
        "/api/notifications",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert response.status_code == 200

    notifications = response.json()

    notification = find_notification(
        notifications,
        ticket_id,
        "NEW_COMMENT",
    )

    assert notification is not None
    assert notification["ticket_id"] == ticket_id
    assert notification["notification_type"] == "NEW_COMMENT"
    assert notification["is_read"] is False


def test_customer_receives_status_changed_notification(client):
    customer_token = get_customer_token(client)
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)

    ticket = create_customer_ticket(
        client,
        customer_token,
        "Notification status change test",
    )

    ticket_id = ticket["id"]

    assign_response = client.patch(
        f"/api/tickets/{ticket_id}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "agent_id": 3,
        },
    )

    assert assign_response.status_code == 200

    status_response = client.patch(
        f"/api/tickets/{ticket_id}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    assert status_response.status_code == 200

    response = client.get(
        "/api/notifications",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert response.status_code == 200

    notifications = response.json()

    notification = find_notification(
        notifications,
        ticket_id,
        "STATUS_CHANGED",
    )

    assert notification is not None
    assert notification["ticket_id"] == ticket_id
    assert notification["notification_type"] == "STATUS_CHANGED"
    assert notification["is_read"] is False


def test_customer_receives_resolved_notification(client):
    customer_token = get_customer_token(client)
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)

    ticket = create_customer_ticket(
        client,
        customer_token,
        "Notification resolved test",
    )

    ticket_id = ticket["id"]

    assign_response = client.patch(
        f"/api/tickets/{ticket_id}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "agent_id": 3,
        },
    )

    assert assign_response.status_code == 200

    progress_response = client.patch(
        f"/api/tickets/{ticket_id}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    assert progress_response.status_code == 200

    resolved_response = client.patch(
        f"/api/tickets/{ticket_id}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "RESOLVED",
        },
    )

    assert resolved_response.status_code == 200

    response = client.get(
        "/api/notifications",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert response.status_code == 200

    notifications = response.json()

    status_notification = find_notification(
        notifications,
        ticket_id,
        "STATUS_CHANGED",
    )

    resolved_notification = find_notification(
        notifications,
        ticket_id,
        "TICKET_RESOLVED",
    )

    assert status_notification is not None
    assert resolved_notification is not None

    assert resolved_notification["ticket_id"] == ticket_id
    assert (
        resolved_notification["notification_type"]
        == "TICKET_RESOLVED"
    )


def test_customer_receives_closed_notification(client):
    customer_token = get_customer_token(client)
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)

    ticket = create_customer_ticket(
        client,
        customer_token,
        "Notification closed test",
    )

    ticket_id = ticket["id"]

    assign_response = client.patch(
        f"/api/tickets/{ticket_id}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "agent_id": 3,
        },
    )

    assert assign_response.status_code == 200

    progress_response = client.patch(
        f"/api/tickets/{ticket_id}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    assert progress_response.status_code == 200

    resolved_response = client.patch(
        f"/api/tickets/{ticket_id}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "RESOLVED",
        },
    )

    assert resolved_response.status_code == 200

    closed_response = client.patch(
        f"/api/tickets/{ticket_id}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "CLOSED",
        },
    )

    assert closed_response.status_code == 200

    response = client.get(
        "/api/notifications",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert response.status_code == 200

    notifications = response.json()

    notification = find_notification(
        notifications,
        ticket_id,
        "TICKET_CLOSED",
    )

    assert notification is not None
    assert notification["ticket_id"] == ticket_id
    assert notification["notification_type"] == "TICKET_CLOSED"
    assert notification["is_read"] is False


def test_user_can_mark_notification_as_read(client):
    customer_token = get_customer_token(client)
    admin_token = get_admin_token(client)

    ticket = create_customer_ticket(
        client,
        customer_token,
        "Notification mark read test",
    )

    ticket_id = ticket["id"]

    response = client.get(
        "/api/notifications",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    notifications = response.json()

    notification = find_notification(
        notifications,
        ticket_id,
        "TICKET_CREATED",
    )

    assert notification is not None

    notification_id = notification["id"]

    assert notification["is_read"] is False

    read_response = client.patch(
        f"/api/notifications/{notification_id}/read",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert read_response.status_code == 200

    updated_notification = read_response.json()

    assert updated_notification["id"] == notification_id
    assert updated_notification["is_read"] is True


def test_user_cannot_mark_another_users_notification_as_read(client):
    customer_token = get_customer_token(client)
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)

    ticket = create_customer_ticket(
        client,
        customer_token,
        "Notification authorization test",
    )

    ticket_id = ticket["id"]

    admin_response = client.get(
        "/api/notifications",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert admin_response.status_code == 200

    admin_notifications = admin_response.json()

    notification = find_notification(
        admin_notifications,
        ticket_id,
        "TICKET_CREATED",
    )

    assert notification is not None

    notification_id = notification["id"]

    agent_response = client.patch(
        f"/api/notifications/{notification_id}/read",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert agent_response.status_code == 404


def test_user_can_mark_all_notifications_as_read(client):
    customer_token = get_customer_token(client)
    admin_token = get_admin_token(client)

    ticket_one = create_customer_ticket(
        client,
        customer_token,
        "Mark all notifications test one",
    )

    ticket_two = create_customer_ticket(
        client,
        customer_token,
        "Mark all notifications test two",
    )

    ticket_one_id = ticket_one["id"]
    ticket_two_id = ticket_two["id"]

    before_response = client.get(
        "/api/notifications",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert before_response.status_code == 200

    notifications_before = before_response.json()

    notification_one = find_notification(
        notifications_before,
        ticket_one_id,
        "TICKET_CREATED",
    )

    notification_two = find_notification(
        notifications_before,
        ticket_two_id,
        "TICKET_CREATED",
    )

    assert notification_one is not None
    assert notification_two is not None

    read_all_response = client.patch(
        "/api/notifications/read-all",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert read_all_response.status_code == 200

    data = read_all_response.json()

    assert data["message"] == "All notifications marked as read"
    assert data["updated_count"] >= 2

    after_response = client.get(
        "/api/notifications",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert after_response.status_code == 200

    notifications_after = after_response.json()

    updated_one = find_notification(
        notifications_after,
        ticket_one_id,
        "TICKET_CREATED",
    )

    updated_two = find_notification(
        notifications_after,
        ticket_two_id,
        "TICKET_CREATED",
    )

    assert updated_one is not None
    assert updated_two is not None

    assert updated_one["is_read"] is True
    assert updated_two["is_read"] is True


def test_notifications_require_authentication(client):
    response = client.get(
        "/api/notifications",
    )

    assert response.status_code in {401, 403}


def test_mark_all_notifications_requires_authentication(client):
    response = client.patch(
        "/api/notifications/read-all",
    )

    assert response.status_code in {401, 403}