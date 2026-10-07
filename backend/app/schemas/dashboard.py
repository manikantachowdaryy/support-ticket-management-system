from pydantic import BaseModel


class TicketStats(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    closed: int
    overdue: int
    critical: int


class AgentTicketStats(BaseModel):
    agent_id: int
    agent_name: str
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int


class AdminDashboardResponse(BaseModel):
    role: str
    tickets: TicketStats
    total_customers: int
    total_support_agents: int
    active_support_agents: int
    tickets_per_agent: list[AgentTicketStats]


class AgentDashboardResponse(BaseModel):
    role: str
    tickets: TicketStats


class CustomerDashboardResponse(BaseModel):
    role: str
    tickets: TicketStats