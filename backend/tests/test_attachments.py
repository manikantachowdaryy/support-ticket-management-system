import io

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


def upload_text_file(
    client: TestClient,
    token: str,
    ticket_id: int = 1,
    filename: str = "test_attachment.txt",
    content: bytes = b"This is a test attachment.",
):
    return client.post(
        f"/api/tickets/{ticket_id}/attachments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        files={
            "file": (
                filename,
                io.BytesIO(content),
                "text/plain",
            )
        },
    )


def test_customer_can_upload_attachment(client):
    token = get_customer_token(client)

    response = upload_text_file(
        client,
        token,
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["ticket_id"] == 1
    assert data["original_filename"] == "test_attachment.txt"
    assert data["file_type"] == "text/plain"
    assert data["file_size"] > 0
    assert data["storage_path"]


def test_agent_can_upload_attachment(client):
    token = get_agent_token(client)

    response = upload_text_file(
        client,
        token,
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["ticket_id"] == 1
    assert data["uploaded_by"] == 3


def test_list_attachments(client):
    token = get_customer_token(client)

    upload_response = upload_text_file(
        client,
        token,
    )

    assert upload_response.status_code == 201

    response = client.get(
        "/api/tickets/1/attachments",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    attachment = data[-1]

    assert attachment["ticket_id"] == 1
    assert attachment["original_filename"] == "test_attachment.txt"
    assert attachment["file_type"] == "text/plain"
    assert attachment["file_size"] > 0
    assert attachment["storage_path"]


def test_download_attachment(client):
    token = get_customer_token(client)

    upload_response = upload_text_file(
        client,
        token,
        content=b"Download test content.",
    )

    assert upload_response.status_code == 201

    attachment_id = upload_response.json()["id"]

    response = client.get(
        f"/api/tickets/attachments/{attachment_id}/download",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.content == b"Download test content."
    assert "text/plain" in response.headers["content-type"]


def test_agent_can_access_assigned_ticket_attachment(client):
    customer_token = get_customer_token(client)

    upload_response = upload_text_file(
        client,
        customer_token,
    )

    assert upload_response.status_code == 201

    attachment_id = upload_response.json()["id"]

    agent_token = get_agent_token(client)

    response = client.get(
        f"/api/tickets/attachments/{attachment_id}/download",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert response.status_code == 200


def test_agent_cannot_access_unassigned_ticket_attachment(client):
    customer_token = get_customer_token(client)

    create_ticket_response = client.post(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "title": "Unassigned attachment access test",
            "description": (
                "Testing agent access to an unassigned ticket attachment."
            ),
            "category_id": 1,
            "priority": "LOW",
        },
    )

    assert create_ticket_response.status_code == 201

    ticket_id = create_ticket_response.json()["id"]

    upload_response = upload_text_file(
        client,
        customer_token,
        ticket_id=ticket_id,
    )

    assert upload_response.status_code == 201

    attachment_id = upload_response.json()["id"]

    agent_token = get_agent_token(client)

    response = client.get(
        f"/api/tickets/attachments/{attachment_id}/download",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert response.status_code == 403


def test_customer_cannot_delete_another_users_attachment(client):
    customer_token = get_customer_token(client)

    upload_response = upload_text_file(
        client,
        customer_token,
    )

    assert upload_response.status_code == 201

    attachment_id = upload_response.json()["id"]

    agent_token = get_agent_token(client)

    response = client.delete(
        f"/api/tickets/attachments/{attachment_id}",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert response.status_code == 403


def test_user_can_delete_own_attachment(client):
    token = get_customer_token(client)

    upload_response = upload_text_file(
        client,
        token,
    )

    assert upload_response.status_code == 201

    attachment_id = upload_response.json()["id"]

    response = client.delete(
        f"/api/tickets/attachments/{attachment_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 204


def test_admin_can_delete_attachment(client):
    customer_token = get_customer_token(client)

    upload_response = upload_text_file(
        client,
        customer_token,
    )

    assert upload_response.status_code == 201

    attachment_id = upload_response.json()["id"]

    admin_token = get_admin_token(client)

    response = client.delete(
        f"/api/tickets/attachments/{attachment_id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 204


def test_reject_unsupported_file_type(client):
    token = get_customer_token(client)

    response = client.post(
        "/api/tickets/1/attachments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        files={
            "file": (
                "malicious.exe",
                io.BytesIO(b"fake executable"),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert "Unsupported file type" in data["detail"]


def test_reject_empty_file(client):
    token = get_customer_token(client)

    response = client.post(
        "/api/tickets/1/attachments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        files={
            "file": (
                "empty.txt",
                io.BytesIO(b""),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Uploaded file is empty"


def test_reject_invalid_pdf_content(client):
    token = get_customer_token(client)

    response = client.post(
        "/api/tickets/1/attachments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        files={
            "file": (
                "invalid.pdf",
                io.BytesIO(b"This is not actually a PDF."),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Invalid PDF file"


def test_reject_oversized_file(client):
    token = get_customer_token(client)

    large_content = b"x" * (10 * 1024 * 1024 + 1)

    response = client.post(
        "/api/tickets/1/attachments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        files={
            "file": (
                "large.txt",
                io.BytesIO(large_content),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "File size cannot exceed 10 MB"


def test_attachment_requires_authentication(client):
    response = client.post(
        "/api/tickets/1/attachments",
        files={
            "file": (
                "unauthenticated.txt",
                io.BytesIO(b"Unauthorized upload"),
                "text/plain",
            )
        },
    )

    assert response.status_code in {401, 403}


def test_attachment_list_requires_authentication(client):
    response = client.get(
        "/api/tickets/1/attachments",
    )

    assert response.status_code in {401, 403}