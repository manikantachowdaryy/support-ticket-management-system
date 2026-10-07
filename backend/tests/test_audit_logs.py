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


def test_admin_can_view_audit_logs(client):
    token = get_admin_token(client)

    response = client.get(
        "/api/audit-logs",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_audit_log_contains_expected_fields(client):
    token = get_admin_token(client)

    response = client.get(
        "/api/audit-logs",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    log = data[0]

    assert "id" in log
    assert "user_id" in log
    assert "action" in log
    assert "entity_type" in log
    assert "entity_id" in log
    assert "ip_address" in log
    assert "metadata_json" in log
    assert "created_at" in log


def test_successful_login_creates_audit_log(client):
    token = get_admin_token(client)

    # The login above should create a LOGIN audit entry.
    response = client.get(
        "/api/audit-logs",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    login_logs = [
        log
        for log in data
        if log["action"] == "LOGIN"
        and log["user_id"] == 2
    ]

    assert len(login_logs) >= 1

    latest_login = login_logs[0]

    assert latest_login["entity_type"] == "AUTHENTICATION"
    assert latest_login["entity_id"] == 2
    assert latest_login["metadata_json"] is not None


def test_customer_cannot_view_audit_logs(client):
    token = get_customer_token(client)

    response = client.get(
        "/api/audit-logs",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403

    data = response.json()

    assert (
        data["detail"]
        == "Only administrators can view audit logs"
    )


def test_agent_cannot_view_audit_logs(client):
    token = get_agent_token(client)

    response = client.get(
        "/api/audit-logs",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403

    data = response.json()

    assert (
        data["detail"]
        == "Only administrators can view audit logs"
    )


def test_audit_logs_require_authentication(client):
    response = client.get(
        "/api/audit-logs",
    )

    assert response.status_code in {401, 403}


def test_audit_logs_are_returned_newest_first(client):
    token = get_admin_token(client)

    response = client.get(
        "/api/audit-logs",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 2

    timestamps = [
        log["created_at"]
        for log in data
    ]

    assert timestamps == sorted(
        timestamps,
        reverse=True,
    )