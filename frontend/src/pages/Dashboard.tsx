import {
    Alert,
    Avatar,
    Box,
    Button,
    Card,
    CardContent,
    CircularProgress,
    Grid,
    Typography,
  } from "@mui/material";
  import {
    AlertCircle,
    CheckCircle2,
    Clock3,
    FolderOpen,
    ListTodo,
    LogOut,
    ShieldAlert,
    Ticket,
    Users,
  } from "lucide-react";
  import { useEffect, useState } from "react";
  import { useNavigate } from "react-router-dom";
  
  import { api } from "../api/axios";
  import { useAuth } from "../context/AuthContext";
  
  interface TicketStats {
    total: number;
    open: number;
    in_progress: number;
    resolved: number;
    closed: number;
    overdue: number;
    critical: number;
  }
  
  interface AgentTicketStats {
    agent_id: number;
    agent_name: string;
    total_tickets: number;
    open_tickets: number;
    in_progress_tickets: number;
    resolved_tickets: number;
    closed_tickets: number;
  }
  
  interface DashboardData {
    role: string;
    tickets: TicketStats;
  
    total_customers?: number;
    total_support_agents?: number;
    active_support_agents?: number;
  
    tickets_per_agent?: AgentTicketStats[];
  }
  
  interface StatCardProps {
    title: string;
    value: number;
    icon: React.ReactNode;
    description: string;
    iconColor: string;
    iconBackground: string;
    onClick?: () => void;
  }
  
  function StatCard({
    title,
    value,
    icon,
    description,
    iconColor,
    iconBackground,
    onClick,
  }: StatCardProps) {
    return (
      <Card
        onClick={onClick}
        sx={{
          height: "100%",
          borderRadius: 4,
          border: "1px solid rgba(15, 23, 42, 0.07)",
          boxShadow: "0 8px 30px rgba(15, 23, 42, 0.06)",
          cursor: onClick ? "pointer" : "default",
          transition: "all 0.25s ease",
          overflow: "hidden",
          background:
            "linear-gradient(145deg, #ffffff 0%, #fbfcff 100%)",
          "&:hover": onClick
            ? {
                transform: "translateY(-5px)",
                boxShadow:
                  "0 14px 35px rgba(15, 23, 42, 0.11)",
                borderColor:
                  "rgba(52, 81, 209, 0.25)",
              }
            : {},
        }}
      >
        <CardContent sx={{ p: 2.8 }}>
          <Box
            sx={{
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "space-between",
            }}
          >
            <Box>
              <Typography
                variant="body2"
                sx={{
                  color: "#64748b",
                  fontWeight: 600,
                  fontSize: "0.88rem",
                }}
              >
                {title}
              </Typography>
  
              <Typography
                variant="h3"
                sx={{
                  mt: 0.8,
                  fontWeight: 800,
                  color: "#0f172a",
                  fontSize: {
                    xs: "2rem",
                    md: "2.25rem",
                  },
                  lineHeight: 1,
                }}
              >
                {value}
              </Typography>
            </Box>
  
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 3,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: iconBackground,
                color: iconColor,
                flexShrink: 0,
              }}
            >
              {icon}
            </Box>
          </Box>
  
          <Typography
            variant="caption"
            sx={{
              display: "block",
              mt: 2.2,
              color: "#64748b",
              fontWeight: 500,
            }}
          >
            {description}
          </Typography>
        </CardContent>
      </Card>
    );
  }
  
  export default function Dashboard() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
  
    const [data, setData] =
      useState<DashboardData | null>(null);
  
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
  
    useEffect(() => {
      const loadDashboard = async () => {
        setLoading(true);
        setError("");
  
        try {
          const response =
            await api.get<DashboardData>("/dashboard");
  
          setData(response.data);
        } catch (err: any) {
          const message =
            err.response?.data?.detail ??
            err.response?.data?.error?.message ??
            "Unable to load dashboard.";
  
          setError(message);
        } finally {
          setLoading(false);
        }
      };
  
      if (user) {
        loadDashboard();
      }
    }, [user]);
  
    if (loading) {
      return (
        <Box
          sx={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background:
              "linear-gradient(135deg, #f8faff 0%, #eef2ff 100%)",
          }}
        >
          <CircularProgress />
        </Box>
      );
    }
  
    if (error) {
      return (
        <Box
          sx={{
            minHeight: "100vh",
            p: 4,
            backgroundColor: "#f8fafc",
          }}
        >
          <Alert severity="error">{error}</Alert>
        </Box>
      );
    }
  
    if (!data || !user) {
      return null;
    }
  
    const roleTitle =
      user.role === "ADMIN"
        ? "Administrator"
        : user.role === "SUPPORT_AGENT"
          ? "Support Agent"
          : "Customer";
  
    const userInitial =
      user.name?.charAt(0)?.toUpperCase() ?? "U";
  
    const handleLogout = async () => {
      await logout();
      navigate("/login", { replace: true });
    };
  
    const goToTickets = () => {
      navigate("/tickets");
    };
  
    const goToTicketFilter = (
      filter: string,
      value: string,
    ) => {
      navigate(
        `/tickets?${filter}=${encodeURIComponent(value)}`,
      );
    };
  
    const ticketStats = data.tickets;
  
    const stats = [
      {
        title: "Total Tickets",
        value: ticketStats.total ?? 0,
        icon: <ListTodo size={23} />,
        description: "All tickets in the system",
        iconColor: "#3451d1",
        iconBackground: "#e9edff",
        onClick: goToTickets,
      },
      {
        title: "Open",
        value: ticketStats.open ?? 0,
        icon: <FolderOpen size={23} />,
        description: "Tickets awaiting action",
        iconColor: "#2563eb",
        iconBackground: "#eaf2ff",
        onClick: () =>
          goToTicketFilter("status", "OPEN"),
      },
      {
        title: "In Progress",
        value: ticketStats.in_progress ?? 0,
        icon: <Clock3 size={23} />,
        description: "Currently being handled",
        iconColor: "#d97706",
        iconBackground: "#fff7e6",
        onClick: () =>
          goToTicketFilter(
            "status",
            "IN_PROGRESS",
          ),
      },
      {
        title: "Resolved",
        value: ticketStats.resolved ?? 0,
        icon: <CheckCircle2 size={23} />,
        description: "Successfully resolved",
        iconColor: "#059669",
        iconBackground: "#e8faf3",
        onClick: () =>
          goToTicketFilter(
            "status",
            "RESOLVED",
          ),
      },
      {
        title: "Closed",
        value: ticketStats.closed ?? 0,
        icon: <CheckCircle2 size={23} />,
        description: "Completed tickets",
        iconColor: "#475569",
        iconBackground: "#f1f5f9",
        onClick: () =>
          goToTicketFilter(
            "status",
            "CLOSED",
          ),
      },
      {
        title: "Overdue",
        value: ticketStats.overdue ?? 0,
        icon: <AlertCircle size={23} />,
        description: "Past SLA deadline",
        iconColor: "#dc2626",
        iconBackground: "#fff0f0",
        onClick: () =>
          navigate("/tickets?overdue=true"),
      },
      {
        title: "Critical",
        value: ticketStats.critical ?? 0,
        icon: <ShieldAlert size={23} />,
        description: "Critical priority tickets",
        iconColor: "#be123c",
        iconBackground: "#fff1f4",
        onClick: () =>
          goToTicketFilter(
            "priority",
            "CRITICAL",
          ),
      },
    ];
  
    return (
      <Box
        sx={{
          minHeight: "100vh",
          background:
            "linear-gradient(135deg, #f8faff 0%, #f1f5ff 45%, #f8fafc 100%)",
          p: {
            xs: 2,
            sm: 3,
            md: 4,
          },
        }}
      >
        <Box
          sx={{
            maxWidth: 1500,
            mx: "auto",
          }}
        >
          {/* Header */}
          <Card
            sx={{
              mb: 4,
              borderRadius: 4,
              overflow: "hidden",
              border:
                "1px solid rgba(52, 81, 209, 0.12)",
              boxShadow:
                "0 12px 40px rgba(52, 81, 209, 0.08)",
              background:
                "linear-gradient(135deg, #ffffff 0%, #f7f9ff 100%)",
            }}
          >
            <CardContent
              sx={{
                p: {
                  xs: 2.5,
                  md: 3.5,
                },
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  flexDirection: {
                    xs: "column",
                    sm: "row",
                  },
                  alignItems: {
                    xs: "flex-start",
                    sm: "center",
                  },
                  justifyContent: "space-between",
                  gap: 2,
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                  }}
                >
                  <Box
                    sx={{
                      width: 56,
                      height: 56,
                      borderRadius: 3,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      background:
                        "linear-gradient(135deg, #3451d1, #6175e8)",
                      color: "#ffffff",
                      boxShadow:
                        "0 8px 20px rgba(52, 81, 209, 0.25)",
                      flexShrink: 0,
                    }}
                  >
                    <Ticket size={28} />
                  </Box>
  
                  <Box>
                    <Typography
                      variant="h4"
                      sx={{
                        fontWeight: 800,
                        color: "#0f172a",
                        fontSize: {
                          xs: "1.7rem",
                          md: "2rem",
                        },
                      }}
                    >
                      Dashboard
                    </Typography>
  
                    <Typography
                      sx={{
                        mt: 0.4,
                        color: "#64748b",
                        fontSize: "0.95rem",
                      }}
                    >
                      Welcome back, {user.name}
                    </Typography>
  
                    <Typography
                      sx={{
                        mt: 0.3,
                        color: "#3451d1",
                        fontSize: "0.82rem",
                        fontWeight: 700,
                      }}
                    >
                      {roleTitle}
                    </Typography>
                  </Box>
                </Box>
  
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1.5,
                  }}
                >
                  <Avatar
                    sx={{
                      width: 40,
                      height: 40,
                      background:
                        "linear-gradient(135deg, #3451d1, #6175e8)",
                      fontWeight: 700,
                    }}
                  >
                    {userInitial}
                  </Avatar>
  
                  <Button
                    variant="outlined"
                    startIcon={<LogOut size={18} />}
                    onClick={handleLogout}
                    sx={{
                      borderRadius: 2.5,
                      textTransform: "none",
                      fontWeight: 700,
                      px: 2,
                      color: "#334155",
                      borderColor: "#cbd5e1",
                      "&:hover": {
                        borderColor: "#dc2626",
                        color: "#dc2626",
                        backgroundColor: "#fff5f5",
                      },
                    }}
                  >
                    Logout
                  </Button>
                </Box>
              </Box>
            </CardContent>
          </Card>
  
          {/* Ticket Overview */}
          <Box sx={{ mb: 4 }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1.2,
                mb: 2,
              }}
            >
              <Box
                sx={{
                  width: 5,
                  height: 24,
                  borderRadius: 2,
                  background:
                    "linear-gradient(180deg, #3451d1, #6175e8)",
                }}
              />
  
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 800,
                  color: "#0f172a",
                }}
              >
                Ticket Overview
              </Typography>
            </Box>
  
            <Grid container spacing={2.5}>
              {stats.map((stat) => (
                <Grid
                  key={stat.title}
                  size={{
                    xs: 12,
                    sm: 6,
                    md: 4,
                    lg: 3,
                  }}
                >
                  <StatCard
                    title={stat.title}
                    value={stat.value}
                    icon={stat.icon}
                    description={stat.description}
                    iconColor={stat.iconColor}
                    iconBackground={
                      stat.iconBackground
                    }
                    onClick={stat.onClick}
                  />
                </Grid>
              ))}
            </Grid>
          </Box>
  
          {/* Admin Section */}
          {user.role === "ADMIN" && (
            <Box sx={{ mb: 4 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1.2,
                  mb: 2,
                }}
              >
                <Box
                  sx={{
                    width: 5,
                    height: 24,
                    borderRadius: 2,
                    background:
                      "linear-gradient(180deg, #7c3aed, #a855f7)",
                  }}
                />
  
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 800,
                    color: "#0f172a",
                  }}
                >
                  User Overview
                </Typography>
              </Box>
  
              <Grid container spacing={2.5}>
                <Grid
                  size={{
                    xs: 12,
                    sm: 6,
                    md: 4,
                  }}
                >
                  <StatCard
                    title="Customers"
                    value={data.total_customers ?? 0}
                    icon={<Users size={23} />}
                    description="Registered customers"
                    iconColor="#7c3aed"
                    iconBackground="#f3eaff"
                    onClick={() =>
                      navigate(
                        "/users?role=CUSTOMER",
                      )
                    }
                  />
                </Grid>
  
                <Grid
                  size={{
                    xs: 12,
                    sm: 6,
                    md: 4,
                  }}
                >
                  <StatCard
                    title="Support Agents"
                    value={
                      data.total_support_agents ?? 0
                    }
                    icon={<Users size={23} />}
                    description="Registered support agents"
                    iconColor="#0891b2"
                    iconBackground="#e6f9fc"
                    onClick={() =>
                      navigate(
                        "/users?role=SUPPORT_AGENT",
                      )
                    }
                  />
                </Grid>
  
                <Grid
                  size={{
                    xs: 12,
                    sm: 6,
                    md: 4,
                  }}
                >
                  <StatCard
                    title="Active Agents"
                    value={
                      data.active_support_agents ?? 0
                    }
                    icon={<CheckCircle2 size={23} />}
                    description="Currently active agents"
                    iconColor="#059669"
                    iconBackground="#e8faf3"
                    onClick={() =>
                      navigate(
                        "/users?role=SUPPORT_AGENT&status=active",
                      )
                    }
                  />
                </Grid>
              </Grid>
  
              {/* Tickets Per Agent */}
              {data.tickets_per_agent &&
                data.tickets_per_agent.length > 0 && (
                  <Card
                    sx={{
                      mt: 3,
                      borderRadius: 4,
                      border:
                        "1px solid rgba(15, 23, 42, 0.07)",
                      boxShadow:
                        "0 8px 30px rgba(15, 23, 42, 0.06)",
                      background:
                        "linear-gradient(145deg, #ffffff 0%, #fbfcff 100%)",
                    }}
                  >
                    <CardContent
                      sx={{
                        p: {
                          xs: 2.5,
                          md: 3,
                        },
                      }}
                    >
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          gap: 1.5,
                          mb: 2.5,
                        }}
                      >
                        <Box
                          sx={{
                            width: 42,
                            height: 42,
                            borderRadius: 2.5,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            backgroundColor:
                              "#e9edff",
                            color: "#3451d1",
                          }}
                        >
                          <Users size={21} />
                        </Box>
  
                        <Box>
                          <Typography
                            variant="h6"
                            sx={{
                              fontWeight: 800,
                              color: "#0f172a",
                            }}
                          >
                            Tickets Per Agent
                          </Typography>
  
                          <Typography
                            variant="body2"
                            sx={{
                              color: "#64748b",
                            }}
                          >
                            Ticket workload across
                            support agents
                          </Typography>
                        </Box>
                      </Box>
  
                      <Box
                        sx={{
                          display: "flex",
                          flexDirection: "column",
                          gap: 1.2,
                        }}
                      >
                        {data.tickets_per_agent.map(
                          (agent) => (
                            <Box
                              key={agent.agent_id}
                              onClick={() =>
                                navigate(
                                  `/tickets?assigned_agent_id=${agent.agent_id}`,
                                )
                              }
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                justifyContent:
                                  "space-between",
                                gap: 2,
                                p: 2,
                                borderRadius: 3,
                                backgroundColor:
                                  "#f8fafc",
                                border:
                                  "1px solid transparent",
                                cursor: "pointer",
                                transition:
                                  "all 0.2s ease",
                                "&:hover": {
                                  backgroundColor:
                                    "#eef2ff",
                                  borderColor:
                                    "#c7d2fe",
                                  transform:
                                    "translateX(3px)",
                                },
                              }}
                            >
                              <Box
                                sx={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: 1.5,
                                }}
                              >
                                <Avatar
                                  sx={{
                                    width: 40,
                                    height: 40,
                                    backgroundColor:
                                      "#e0e7ff",
                                    color: "#3451d1",
                                    fontWeight: 700,
                                  }}
                                >
                                  {agent.agent_name
                                    .charAt(0)
                                    .toUpperCase()}
                                </Avatar>
  
                                <Box>
                                  <Typography
                                    sx={{
                                      fontWeight: 700,
                                      color:
                                        "#1e293b",
                                    }}
                                  >
                                    {agent.agent_name}
                                  </Typography>
  
                                  <Typography
                                    variant="caption"
                                    sx={{
                                      color:
                                        "#64748b",
                                    }}
                                  >
                                    Agent #
                                    {agent.agent_id}
                                  </Typography>
                                </Box>
                              </Box>
  
                              <Box
                                sx={{
                                  minWidth: 55,
                                  textAlign: "center",
                                  px: 1.5,
                                  py: 0.8,
                                  borderRadius: 2,
                                  backgroundColor:
                                    "#e9edff",
                                  color: "#3451d1",
                                }}
                              >
                                <Typography
                                  sx={{
                                    fontWeight: 800,
                                    fontSize:
                                      "1.05rem",
                                  }}
                                >
                                  {
                                    agent.total_tickets
                                  }
                                </Typography>
  
                                <Typography
                                  variant="caption"
                                  sx={{
                                    fontWeight: 600,
                                  }}
                                >
                                  tickets
                                </Typography>
                              </Box>
                            </Box>
                          ),
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                )}
            </Box>
          )}
  
          {/* Support Agent Section */}
          {user.role === "SUPPORT_AGENT" && (
            <Box sx={{ mb: 4 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1.2,
                  mb: 2,
                }}
              >
                <Box
                  sx={{
                    width: 5,
                    height: 24,
                    borderRadius: 2,
                    background:
                      "linear-gradient(180deg, #0891b2, #22c1dc)",
                  }}
                />
  
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 800,
                    color: "#0f172a",
                  }}
                >
                  My Ticket Summary
                </Typography>
              </Box>
  
              <Grid container spacing={2.5}>
                <Grid
                  size={{
                    xs: 12,
                    sm: 6,
                    md: 4,
                  }}
                >
                  <StatCard
                    title="My Open Tickets"
                    value={ticketStats.open ?? 0}
                    icon={<FolderOpen size={23} />}
                    description="Tickets assigned to you"
                    iconColor="#2563eb"
                    iconBackground="#eaf2ff"
                    onClick={() =>
                      navigate(
                        "/tickets?status=OPEN",
                      )
                    }
                  />
                </Grid>
  
                <Grid
                  size={{
                    xs: 12,
                    sm: 6,
                    md: 4,
                  }}
                >
                  <StatCard
                    title="My Overdue Tickets"
                    value={ticketStats.overdue ?? 0}
                    icon={<AlertCircle size={23} />}
                    description="Assigned tickets past SLA"
                    iconColor="#dc2626"
                    iconBackground="#fff0f0"
                    onClick={() =>
                      navigate(
                        "/tickets?overdue=true",
                      )
                    }
                  />
                </Grid>
  
                <Grid
                  size={{
                    xs: 12,
                    sm: 6,
                    md: 4,
                  }}
                >
                  <StatCard
                    title="My Resolved Tickets"
                    value={ticketStats.resolved ?? 0}
                    icon={<CheckCircle2 size={23} />}
                    description="Tickets resolved by you"
                    iconColor="#059669"
                    iconBackground="#e8faf3"
                    onClick={() =>
                      navigate(
                        "/tickets?status=RESOLVED",
                      )
                    }
                  />
                </Grid>
              </Grid>
            </Box>
          )}
  
          {/* Customer Section */}
          {user.role === "CUSTOMER" && (
            <Card
              sx={{
                borderRadius: 4,
                border:
                  "1px solid rgba(15, 23, 42, 0.07)",
                boxShadow:
                  "0 8px 30px rgba(15, 23, 42, 0.06)",
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1.5,
                  }}
                >
                  <Box
                    sx={{
                      width: 44,
                      height: 44,
                      borderRadius: 2.5,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      backgroundColor: "#e9edff",
                      color: "#3451d1",
                    }}
                  >
                    <Ticket size={22} />
                  </Box>
  
                  <Box>
                    <Typography
                      variant="h6"
                      sx={{
                        fontWeight: 800,
                        color: "#0f172a",
                      }}
                    >
                      My Tickets
                    </Typography>
  
                    <Typography
                      variant="body2"
                      sx={{
                        color: "#64748b",
                        mt: 0.3,
                      }}
                    >
                      View and manage your support
                      tickets from the Tickets section.
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          )}
        </Box>
      </Box>
    );
  }