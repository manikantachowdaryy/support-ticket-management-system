from datetime import datetime, timedelta
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


def unique_text(prefix: str) -> str:
    return f"{prefix} {uuid.uuid4().hex[:10]}"


def get_active_category_id(
    client: TestClient,
    token: str,
) -> int:
    response = client.get(
        "/api/categories",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    categories = response.json()

    for category in categories:
        if category["is_active"]:
            return category["id"]

    raise AssertionError("No active category available")


def create_category(
    client: TestClient,
    admin_token: str,
    name: str | None = None,
) -> dict:
    if name is None:
        name = unique_text("Ticket Test Category")

    response = client.post(
        "/api/categories",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": name,
            "description": "Category for ticket testing",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_ticket(
    client: TestClient,
    customer_token: str,
    category_id: int,
    title: str | None = None,
    description: str = "Ticket created during automated testing",
    priority: str = "MEDIUM",
) -> dict:
    if title is None:
        title = unique_text("Test Ticket")

    response = client.post(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "title": title,
            "description": description,
            "category_id": category_id,
            "priority": priority,
        },
    )

    assert response.status_code == 201

    return response.json()


def assign_ticket(
    client: TestClient,
    admin_token: str,
    ticket_id: int,
    agent_id: int = 3,
) -> dict:
    response = client.patch(
        f"/api/tickets/{ticket_id}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "agent_id": agent_id,
        },
    )

    assert response.status_code == 200

    return response.json()


def get_seed_agent_id(
    client: TestClient,
    admin_token: str,
) -> int:
    response = client.get(
        "/api/users",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    users = response.json()

    for user in users:
        if (
            user["email"] == AGENT_EMAIL
            and user["role"] == "SUPPORT_AGENT"
        ):
            return user["id"]

    raise AssertionError("Seed support agent not found")


def create_support_agent(
    client: TestClient,
    admin_token: str,
) -> dict:
    email = f"ticket_agent_{uuid.uuid4().hex[:10]}@test.com"

    response = client.post(
        "/api/users",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "Ticket Test Agent",
            "email": email,
            "password": "TestAgent@123",
            "role": "SUPPORT_AGENT",
        },
    )

    assert response.status_code == 201

    return response.json()


# ---------------------------------------------------------------------------
# Ticket Creation
# ---------------------------------------------------------------------------


def test_customer_can_create_ticket(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
        title=unique_text("Customer Created Ticket"),
        priority="HIGH",
    )

    assert ticket["id"] > 0
    assert ticket["ticket_number"].startswith("TKT-")
    assert ticket["title"].startswith("Customer Created Ticket")
    assert ticket["priority"] == "HIGH"
    assert ticket["status"] == "OPEN"
    assert ticket["customer_id"] > 0
    assert ticket["category_id"] == category_id
    assert ticket["due_date"] is not None
    assert ticket["created_at"] is not None
    assert ticket["updated_at"] is not None


def test_admin_cannot_create_ticket(client):
    admin_token = get_admin_token(client)
    category_id = get_active_category_id(
        client,
        admin_token,
    )

    response = client.post(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "title": unique_text("Admin Ticket"),
            "description": "Admin should not create tickets",
            "category_id": category_id,
            "priority": "LOW",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only customers can create tickets"


def test_support_agent_cannot_create_ticket(client):
    agent_token = get_agent_token(client)
    category_id = get_active_category_id(
        client,
        agent_token,
    )

    response = client.post(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "title": unique_text("Agent Ticket"),
            "description": "Agent should not create tickets",
            "category_id": category_id,
            "priority": "LOW",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only customers can create tickets"


def test_unauthenticated_user_cannot_create_ticket(client):
    response = client.post(
        "/api/tickets",
        json={
            "title": "Unauthenticated Ticket",
            "description": "Should fail",
            "category_id": 1,
            "priority": "LOW",
        },
    )

    assert response.status_code in {401, 403}


def test_ticket_creation_rejects_inactive_category(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_text("Inactive Ticket Category"),
    )

    deactivate_response = client.patch(
        f"/api/categories/{category['id']}/deactivate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False

    response = client.post(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "title": unique_text("Inactive Category Ticket"),
            "description": "Should reject inactive category",
            "category_id": category["id"],
            "priority": "MEDIUM",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Category not found or inactive"


def test_ticket_creation_rejects_invalid_priority(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    response = client.post(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "title": unique_text("Invalid Priority Ticket"),
            "description": "Should reject invalid priority",
            "category_id": category_id,
            "priority": "URGENT",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid priority"


def test_ticket_priority_is_case_insensitive(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    response = client.post(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "title": unique_text("Case Priority Ticket"),
            "description": "Priority case test",
            "category_id": category_id,
            "priority": "critical",
        },
    )

    assert response.status_code == 201
    assert response.json()["priority"] == "CRITICAL"


# ---------------------------------------------------------------------------
# SLA
# ---------------------------------------------------------------------------


def test_low_priority_sla_is_72_hours(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
        priority="LOW",
    )

    created_at = datetime.fromisoformat(
        ticket["created_at"].replace("Z", "+00:00")
    )

    due_date = datetime.fromisoformat(
        ticket["due_date"].replace("Z", "+00:00")
    )

    difference = due_date - created_at

    assert difference == timedelta(hours=72)


def test_medium_priority_sla_is_48_hours(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
        priority="MEDIUM",
    )

    created_at = datetime.fromisoformat(
        ticket["created_at"].replace("Z", "+00:00")
    )

    due_date = datetime.fromisoformat(
        ticket["due_date"].replace("Z", "+00:00")
    )

    assert due_date - created_at == timedelta(hours=48)


def test_high_priority_sla_is_24_hours(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
        priority="HIGH",
    )

    created_at = datetime.fromisoformat(
        ticket["created_at"].replace("Z", "+00:00")
    )

    due_date = datetime.fromisoformat(
        ticket["due_date"].replace("Z", "+00:00")
    )

    assert due_date - created_at == timedelta(hours=24)


def test_critical_priority_sla_is_4_hours(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
        priority="CRITICAL",
    )

    created_at = datetime.fromisoformat(
        ticket["created_at"].replace("Z", "+00:00")
    )

    due_date = datetime.fromisoformat(
        ticket["due_date"].replace("Z", "+00:00")
    )

    assert due_date - created_at == timedelta(hours=4)


# ---------------------------------------------------------------------------
# Get Ticket / Resource Authorization
# ---------------------------------------------------------------------------


def test_customer_can_get_own_ticket(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    response = client.get(
        f"/api/tickets/{ticket['id']}",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == ticket["id"]


def test_admin_can_get_any_ticket(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    response = client.get(
        f"/api/tickets/{ticket['id']}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == ticket["id"]


def test_unassigned_agent_cannot_get_ticket(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    response = client.get(
        f"/api/tickets/{ticket['id']}",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have access to this ticket"


def test_customer_cannot_get_another_customers_ticket(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    second_customer = client.post(
        "/api/users",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "Second Ticket Customer",
            "email": f"second_customer_{uuid.uuid4().hex[:10]}@test.com",
            "password": "SecondCustomer@123",
            "role": "CUSTOMER",
        },
    )

    assert second_customer.status_code == 201

    second_customer_email = second_customer.json()["email"]

    second_customer_login = client.post(
        "/api/auth/login",
        json={
            "email": second_customer_email,
            "password": "SecondCustomer@123",
        },
    )

    assert second_customer_login.status_code == 200

    second_customer_token = second_customer_login.json()["access_token"]

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    response = client.get(
        f"/api/tickets/{ticket['id']}",
        headers={
            "Authorization": f"Bearer {second_customer_token}"
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have access to this ticket"


def test_get_nonexistent_ticket_returns_404(client):
    customer_token = get_customer_token(client)

    response = client.get(
        "/api/tickets/999999999",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Ticket not found"


# ---------------------------------------------------------------------------
# Ticket Update
# ---------------------------------------------------------------------------


def test_customer_can_update_own_ticket(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    response = client.put(
        f"/api/tickets/{ticket['id']}",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "title": "Updated Ticket Title",
            "description": "Updated ticket description",
            "priority": "HIGH",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == ticket["id"]
    assert data["title"] == "Updated Ticket Title"
    assert data["description"] == "Updated ticket description"
    assert data["priority"] == "HIGH"


def test_ticket_update_rejects_inactive_category(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    active_category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        active_category_id,
    )

    category = create_category(
        client,
        admin_token,
        name=unique_text("Inactive Update Category"),
    )

    deactivate_response = client.patch(
        f"/api/categories/{category['id']}/deactivate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert deactivate_response.status_code == 200

    response = client.put(
        f"/api/tickets/{ticket['id']}",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "category_id": category["id"],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Category not found or inactive"


def test_ticket_update_rejects_invalid_priority(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    response = client.put(
        f"/api/tickets/{ticket['id']}",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "priority": "URGENT",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid priority"


# ---------------------------------------------------------------------------
# Listing / Search / Filtering
# ---------------------------------------------------------------------------


def test_customer_can_list_own_tickets(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    create_ticket(
        client,
        customer_token,
        category_id,
        title=unique_text("Customer List Ticket"),
    )

    response = client.get(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total" in data
    assert "total_pages" in data

    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total"] >= 1
    assert data["total_pages"] >= 1


def test_admin_can_list_all_tickets(client):
    admin_token = get_admin_token(client)

    response = client.get(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["items"], list)
    assert data["total"] >= len(data["items"])


def test_support_agent_only_lists_assigned_tickets(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
        title=unique_text("Assigned Agent List Ticket"),
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    assign_ticket(
        client,
        admin_token,
        ticket["id"],
        agent_id,
    )

    response = client.get(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == ticket["id"]
        for item in data["items"]
    )


def test_ticket_search_by_title(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    unique_title = unique_text("Unique Login Search")

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
        title=unique_title,
    )

    response = client.get(
        "/api/tickets",
        params={
            "search": unique_title,
        },
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == ticket["id"]
        for item in data["items"]
    )


def test_ticket_filter_by_priority(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
        priority="CRITICAL",
    )

    response = client.get(
        "/api/tickets",
        params={
            "priority": "critical",
        },
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    assert all(
        item["priority"] == "CRITICAL"
        for item in data["items"]
    )

    assert any(
        item["id"] == ticket["id"]
        for item in data["items"]
    )


def test_ticket_filter_by_status(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    assign_ticket(
        client,
        admin_token,
        ticket["id"],
        agent_id,
    )

    response = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    assert response.status_code == 200

    list_response = client.get(
        "/api/tickets",
        params={
            "status": "in_progress",
        },
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert list_response.status_code == 200

    data = list_response.json()

    assert any(
        item["id"] == ticket["id"]
        for item in data["items"]
    )


def test_ticket_filter_by_category(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category = create_category(
        client,
        admin_token,
        name=unique_text("Filter Category"),
    )

    ticket = create_ticket(
        client,
        customer_token,
        category["id"],
    )

    response = client.get(
        "/api/tickets",
        params={
            "category_id": category["id"],
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == ticket["id"]
        for item in data["items"]
    )


def test_ticket_filter_by_assigned_agent(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    assign_ticket(
        client,
        admin_token,
        ticket["id"],
        agent_id,
    )

    response = client.get(
        "/api/tickets",
        params={
            "assigned_agent_id": agent_id,
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == ticket["id"]
        for item in data["items"]
    )


def test_ticket_filter_by_customer(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    response = client.get(
        "/api/tickets",
        params={
            "customer_id": ticket["customer_id"],
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        item["customer_id"] == ticket["customer_id"]
        for item in data["items"]
    )


def test_ticket_pagination(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    for index in range(3):
        create_ticket(
            client,
            customer_token,
            category_id,
            title=f"Pagination Ticket {uuid.uuid4().hex[:8]} {index}",
        )

    response = client.get(
        "/api/tickets",
        params={
            "page": 1,
            "page_size": 2,
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) <= 2
    assert data["total_pages"] >= 1


def test_ticket_sorting_by_title_ascending(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    title_one = unique_text("AAA Ticket")
    title_two = unique_text("ZZZ Ticket")

    create_ticket(
        client,
        customer_token,
        category_id,
        title=title_two,
    )

    create_ticket(
        client,
        customer_token,
        category_id,
        title=title_one,
    )

    response = client.get(
        "/api/tickets",
        params={
            "sort_by": "title",
            "sort_order": "asc",
            "page_size": 100,
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    titles = [
        item["title"]
        for item in response.json()["items"]
    ]

    assert titles == sorted(titles)


def test_ticket_sorting_by_title_descending(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    title_one = unique_text("AAA Desc Ticket")
    title_two = unique_text("ZZZ Desc Ticket")

    create_ticket(
        client,
        customer_token,
        category_id,
        title=title_one,
    )

    create_ticket(
        client,
        customer_token,
        category_id,
        title=title_two,
    )

    response = client.get(
        "/api/tickets",
        params={
            "sort_by": "title",
            "sort_order": "desc",
            "page_size": 100,
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    titles = [
        item["title"]
        for item in response.json()["items"]
    ]

    assert titles == sorted(
        titles,
        reverse=True,
    )


# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------


def test_admin_can_assign_ticket(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    response = client.patch(
        f"/api/tickets/{ticket['id']}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "agent_id": agent_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["assigned_agent_id"] == agent_id


def test_support_agent_can_assign_ticket(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    response = client.patch(
        f"/api/tickets/{ticket['id']}/assign",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "agent_id": agent_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["assigned_agent_id"] == agent_id


def test_customer_cannot_assign_ticket(client):
    customer_token = get_customer_token(client)
    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    response = client.patch(
        f"/api/tickets/{ticket['id']}/assign",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "agent_id": 3,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to assign tickets"
    )


def test_assignment_rejects_inactive_agent(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    agent = create_support_agent(
        client,
        admin_token,
    )

    deactivate_response = client.patch(
        f"/api/users/{agent['id']}/deactivate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert deactivate_response.status_code == 200

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    response = client.patch(
        f"/api/tickets/{ticket['id']}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "agent_id": agent["id"],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Agent not found or inactive"


def test_assignment_rejects_customer_as_agent(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    response = client.patch(
        f"/api/tickets/{ticket['id']}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "agent_id": 1,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Selected user is not a support agent"
    )


def test_ticket_can_be_reassigned(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    first_agent = create_support_agent(
        client,
        admin_token,
    )

    second_agent = create_support_agent(
        client,
        admin_token,
    )

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    first_assignment = client.patch(
        f"/api/tickets/{ticket['id']}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "agent_id": first_agent["id"],
        },
    )

    assert first_assignment.status_code == 200

    second_assignment = client.patch(
        f"/api/tickets/{ticket['id']}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "agent_id": second_agent["id"],
        },
    )

    assert second_assignment.status_code == 200
    assert second_assignment.json()["assigned_agent_id"] == second_agent["id"]


# ---------------------------------------------------------------------------
# Status Workflow
# ---------------------------------------------------------------------------


def test_agent_can_move_ticket_from_open_to_in_progress(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    assign_ticket(
        client,
        admin_token,
        ticket["id"],
        agent_id,
    )

    response = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


def test_agent_can_move_ticket_to_resolved(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    assign_ticket(
        client,
        admin_token,
        ticket["id"],
        agent_id,
    )

    in_progress = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    assert in_progress.status_code == 200

    resolved = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "RESOLVED",
        },
    )

    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"


def test_resolved_ticket_can_be_reopened(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    assign_ticket(
        client,
        admin_token,
        ticket["id"],
        agent_id,
    )

    client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    resolved = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "RESOLVED",
        },
    )

    assert resolved.status_code == 200

    reopened = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "OPEN",
        },
    )

    assert reopened.status_code == 200
    assert reopened.json()["status"] == "OPEN"


def test_resolved_ticket_can_be_closed(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    assign_ticket(
        client,
        admin_token,
        ticket["id"],
        agent_id,
    )

    client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    resolved = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "RESOLVED",
        },
    )

    assert resolved.status_code == 200

    closed = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "CLOSED",
        },
    )

    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"


def test_invalid_open_to_resolved_transition_is_rejected(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    assign_ticket(
        client,
        admin_token,
        ticket["id"],
        agent_id,
    )

    response = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "RESOLVED",
        },
    )

    assert response.status_code == 400


def test_invalid_open_to_closed_transition_is_rejected(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    assign_ticket(
        client,
        admin_token,
        ticket["id"],
        agent_id,
    )

    response = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "CLOSED",
        },
    )

    assert response.status_code == 400


def test_closed_ticket_cannot_change_status(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    assign_ticket(
        client,
        admin_token,
        ticket["id"],
        agent_id,
    )

    client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "RESOLVED",
        },
    )

    closed = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "CLOSED",
        },
    )

    assert closed.status_code == 200

    reopen = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "OPEN",
        },
    )

    assert reopen.status_code == 400


def test_customer_cannot_change_ticket_status(client):
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    response = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Only admins and support agents can change ticket status"
    )


def test_unassigned_agent_cannot_change_ticket_status(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    assert ticket["assigned_agent_id"] is None
    assert agent_id > 0

    response = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You can only change status of tickets assigned to you"
    )


def test_admin_can_change_ticket_status(client):
    admin_token = get_admin_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    response = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


# ---------------------------------------------------------------------------
# Status History
# ---------------------------------------------------------------------------


def test_ticket_status_history_is_recorded(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    assign_ticket(
        client,
        admin_token,
        ticket["id"],
        agent_id,
    )

    response = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    assert response.status_code == 200

    history_response = client.get(
        f"/api/tickets/{ticket['id']}/status-history",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) >= 1

    latest = history[-1]

    assert latest["ticket_id"] == ticket["id"]
    assert latest["old_status"] == "OPEN"
    assert latest["new_status"] == "IN_PROGRESS"
    assert latest["changed_by"] == agent_id


def test_customer_can_view_own_ticket_status_history(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    agent_id = get_seed_agent_id(
        client,
        admin_token,
    )

    assign_ticket(
        client,
        admin_token,
        ticket["id"],
        agent_id,
    )

    client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    response = client.get(
        f"/api/tickets/{ticket['id']}/status-history",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_unassigned_agent_cannot_view_ticket_status_history(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    response = client.get(
        f"/api/tickets/{ticket['id']}/status-history",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Assignment Restrictions on Closed Tickets
# ---------------------------------------------------------------------------

def test_closed_ticket_cannot_be_reassigned(client):
    admin_token = get_admin_token(client)
    agent_token = get_agent_token(client)
    customer_token = get_customer_token(client)

    category_id = get_active_category_id(
        client,
        customer_token,
    )

    ticket = create_ticket(
        client,
        customer_token,
        category_id,
    )

    # Get the seeded support agent that matches agent_token.
    agent_me_response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
    )

    assert agent_me_response.status_code == 200

    agent_id = agent_me_response.json()["id"]

    # Assign the ticket to the same agent whose token
    # will be used for the status changes.
    assigned = assign_ticket(
        client,
        admin_token,
        ticket["id"],
        agent_id,
    )

    assert assigned["assigned_agent_id"] == agent_id

    # OPEN -> IN_PROGRESS
    in_progress = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "IN_PROGRESS",
        },
    )

    assert in_progress.status_code == 200
    assert in_progress.json()["status"] == "IN_PROGRESS"

    # IN_PROGRESS -> RESOLVED
    resolved = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "RESOLVED",
        },
    )

    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"

    # RESOLVED -> CLOSED
    closed = client.patch(
        f"/api/tickets/{ticket['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}"
        },
        json={
            "status": "CLOSED",
        },
    )

    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"

    # Create another active support agent.
    another_agent = create_support_agent(
        client,
        admin_token,
    )

    # A closed ticket must not be reassigned.
    reassign_response = client.patch(
        f"/api/tickets/{ticket['id']}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "assigned_agent_id": another_agent["id"],
        },
    )

    assert reassign_response.status_code == 400