import { useCallback, useEffect, useState } from "react";
import {
  useNavigate,
  useSearchParams,
} from "react-router-dom";

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

import {
  AlertCircle,
  ArrowDownAZ,
  ArrowUpAZ,
  CalendarDays,
  ChevronRight,
  Filter,
  ListFilter,
  Search,
  Ticket as TicketIcon,
  UserRound,
  X,
} from "lucide-react";

import axios from "axios";

import { api } from "../api/axios";
import { useAuth } from "../context/AuthContext";

interface Ticket {
  id: number;
  ticket_number: string;
  title: string;
  description: string;
  customer_id: number;
  assigned_agent_id: number | null;
  category_id: number;
  priority: string;
  status: string;
  due_date: string;
  created_at: string;
  updated_at: string;
}

interface TicketListResponse {
  items: Ticket[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "OPEN", label: "Open" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "RESOLVED", label: "Resolved" },
  { value: "CLOSED", label: "Closed" },
];

const PRIORITY_OPTIONS = [
  { value: "", label: "All Priorities" },
  { value: "LOW", label: "Low" },
  { value: "MEDIUM", label: "Medium" },
  { value: "HIGH", label: "High" },
  { value: "CRITICAL", label: "Critical" },
];

const SORT_OPTIONS = [
  {
    value: "created_at",
    label: "Created Date",
  },
  {
    value: "updated_at",
    label: "Updated Date",
  },
  {
    value: "title",
    label: "Title",
  },
  {
    value: "priority",
    label: "Priority",
  },
  {
    value: "status",
    label: "Status",
  },
  {
    value: "due_date",
    label: "Due Date",
  },
];

function formatStatus(value: string) {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}

function formatDate(value: string) {
  return new Date(value).toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function getStatusStyles(status: string) {
  switch (status) {
    case "OPEN":
      return {
        background: "#eaf2ff",
        color: "#2563eb",
        border: "#bfdbfe",
      };

    case "IN_PROGRESS":
      return {
        background: "#fff7e6",
        color: "#d97706",
        border: "#fde68a",
      };

    case "RESOLVED":
      return {
        background: "#e8faf3",
        color: "#059669",
        border: "#a7f3d0",
      };

    case "CLOSED":
      return {
        background: "#f1f5f9",
        color: "#475569",
        border: "#cbd5e1",
      };

    default:
      return {
        background: "#f8fafc",
        color: "#64748b",
        border: "#e2e8f0",
      };
  }
}

function getPriorityStyles(priority: string) {
  switch (priority) {
    case "CRITICAL":
      return {
        background: "#fff1f2",
        color: "#be123c",
        border: "#fecdd3",
      };

    case "HIGH":
      return {
        background: "#fff7ed",
        color: "#c2410c",
        border: "#fed7aa",
      };

    case "MEDIUM":
      return {
        background: "#fffbea",
        color: "#a16207",
        border: "#fde68a",
      };

    case "LOW":
      return {
        background: "#f1f5f9",
        color: "#475569",
        border: "#cbd5e1",
      };

    default:
      return {
        background: "#f8fafc",
        color: "#64748b",
        border: "#e2e8f0",
      };
  }
}

function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    return (
      error.message ||
      "Something went wrong."
    );
  }

  return "Something went wrong.";
}

function isTicketOverdue(ticket: Ticket) {
  if (
    ticket.status === "RESOLVED" ||
    ticket.status === "CLOSED"
  ) {
    return false;
  }

  return (
    new Date(ticket.due_date).getTime() <
    Date.now()
  );
}

export default function Tickets() {
  const navigate = useNavigate();

  const [searchParams, setSearchParams] =
    useSearchParams();

  const { user } = useAuth();

  const [tickets, setTickets] = useState<Ticket[]>(
    [],
  );

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [page, setPage] = useState(
    Number(searchParams.get("page") ?? "1"),
  );

  const [pageSize, setPageSize] = useState(
    Number(
      searchParams.get("page_size") ?? "20",
    ),
  );

  const [search, setSearch] = useState(
    searchParams.get("search") ?? "",
  );

  const [status, setStatus] = useState(
    searchParams.get("status") ?? "",
  );

  const [priority, setPriority] = useState(
    searchParams.get("priority") ?? "",
  );

  const [categoryId, setCategoryId] =
    useState(
      searchParams.get("category_id") ?? "",
    );

  const [assignedAgentId, setAssignedAgentId] =
    useState(
      searchParams.get("assigned_agent_id") ??
        "",
    );

  const [customerId, setCustomerId] = useState(
    searchParams.get("customer_id") ?? "",
  );

  const [sortBy, setSortBy] = useState(
    searchParams.get("sort_by") ??
      "created_at",
  );

  const [sortOrder, setSortOrder] = useState(
    searchParams.get("sort_order") ?? "desc",
  );

  const [total, setTotal] = useState(0);

  const updateUrl = useCallback(
    (
      values: {
        page?: number;
        page_size?: number;
        search?: string;
        status?: string;
        priority?: string;
        category_id?: string;
        assigned_agent_id?: string;
        customer_id?: string;
        sort_by?: string;
        sort_order?: string;
      } = {},
    ) => {
      const params = new URLSearchParams();

      const nextPage = values.page ?? page;
      const nextPageSize =
        values.page_size ?? pageSize;
      const nextSearch =
        values.search ?? search;
      const nextStatus =
        values.status ?? status;
      const nextPriority =
        values.priority ?? priority;
      const nextCategoryId =
        values.category_id ?? categoryId;
      const nextAssignedAgentId =
        values.assigned_agent_id ??
        assignedAgentId;
      const nextCustomerId =
        values.customer_id ?? customerId;
      const nextSortBy =
        values.sort_by ?? sortBy;
      const nextSortOrder =
        values.sort_order ?? sortOrder;

      if (nextPage > 1) {
        params.set(
          "page",
          String(nextPage),
        );
      }

      if (nextPageSize !== 20) {
        params.set(
          "page_size",
          String(nextPageSize),
        );
      }

      if (nextSearch.trim()) {
        params.set(
          "search",
          nextSearch.trim(),
        );
      }

      if (nextStatus) {
        params.set(
          "status",
          nextStatus,
        );
      }

      if (nextPriority) {
        params.set(
          "priority",
          nextPriority,
        );
      }

      if (nextCategoryId) {
        params.set(
          "category_id",
          nextCategoryId,
        );
      }

      if (nextAssignedAgentId) {
        params.set(
          "assigned_agent_id",
          nextAssignedAgentId,
        );
      }

      if (nextCustomerId) {
        params.set(
          "customer_id",
          nextCustomerId,
        );
      }

      if (nextSortBy !== "created_at") {
        params.set(
          "sort_by",
          nextSortBy,
        );
      }

      if (nextSortOrder !== "desc") {
        params.set(
          "sort_order",
          nextSortOrder,
        );
      }

      setSearchParams(params);
    },
    [
      page,
      pageSize,
      search,
      status,
      priority,
      categoryId,
      assignedAgentId,
      customerId,
      sortBy,
      sortOrder,
      setSearchParams,
    ],
  );

  const loadTickets = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response =
        await api.get<TicketListResponse>(
          "/tickets",
          {
            params: {
              page,
              page_size: pageSize,
              search:
                search.trim() || undefined,
              status:
                status || undefined,
              priority:
                priority || undefined,
              category_id:
                categoryId || undefined,
              assigned_agent_id:
                assignedAgentId || undefined,
              customer_id:
                customerId || undefined,
              sort_by: sortBy,
              sort_order: sortOrder,
            },
          },
        );

      setTickets(response.data.items);
      setTotal(response.data.total);
    } catch (err) {
      setError(getErrorMessage(err));
      setTickets([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [
    page,
    pageSize,
    search,
    status,
    priority,
    categoryId,
    assignedAgentId,
    customerId,
    sortBy,
    sortOrder,
  ]);

  useEffect(() => {
    void loadTickets();
  }, [loadTickets]);

  const handleSearch = () => {
    setPage(1);

    updateUrl({
      page: 1,
      search,
    });
  };

  const handleStatusChange = (
    value: string,
  ) => {
    setStatus(value);
    setPage(1);

    updateUrl({
      page: 1,
      status: value,
    });
  };

  const handlePriorityChange = (
    value: string,
  ) => {
    setPriority(value);
    setPage(1);

    updateUrl({
      page: 1,
      priority: value,
    });
  };

  const handleCategoryChange = (
    value: string,
  ) => {
    setCategoryId(value);
    setPage(1);

    updateUrl({
      page: 1,
      category_id: value,
    });
  };

  const handleAgentChange = (
    value: string,
  ) => {
    setAssignedAgentId(value);
    setPage(1);

    updateUrl({
      page: 1,
      assigned_agent_id: value,
    });
  };

  const handleCustomerChange = (
    value: string,
  ) => {
    setCustomerId(value);
    setPage(1);

    updateUrl({
      page: 1,
      customer_id: value,
    });
  };

  const handleSortByChange = (
    value: string,
  ) => {
    setSortBy(value);
    setPage(1);

    updateUrl({
      page: 1,
      sort_by: value,
    });
  };

  const handleSortOrderChange = (
    value: string,
  ) => {
    setSortOrder(value);
    setPage(1);

    updateUrl({
      page: 1,
      sort_order: value,
    });
  };

  const handleResetFilters = () => {
    setSearch("");
    setStatus("");
    setPriority("");
    setCategoryId("");
    setAssignedAgentId("");
    setCustomerId("");
    setSortBy("created_at");
    setSortOrder("desc");
    setPage(1);

    setSearchParams({});
  };

  const handlePageChange = (
    _event: unknown,
    newPage: number,
  ) => {
    const nextPage = newPage + 1;

    setPage(nextPage);

    updateUrl({
      page: nextPage,
    });
  };

  const handleRowsPerPageChange = (
    event: React.ChangeEvent<
      HTMLTextAreaElement | HTMLInputElement
    >,
  ) => {
    const nextPageSize = Number(
      event.target.value,
    );

    setPageSize(nextPageSize);
    setPage(1);

    updateUrl({
      page: 1,
      page_size: nextPageSize,
    });
  };

  const hasFilters =
    Boolean(search.trim()) ||
    Boolean(status) ||
    Boolean(priority) ||
    Boolean(categoryId) ||
    Boolean(assignedAgentId) ||
    Boolean(customerId);

  const openCount = tickets.filter(
    (ticket) => ticket.status === "OPEN",
  ).length;

  const inProgressCount = tickets.filter(
    (ticket) =>
      ticket.status === "IN_PROGRESS",
  ).length;

  const overdueCount = tickets.filter(
    (ticket) => isTicketOverdue(ticket),
  ).length;

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
            mb: 3,
            borderRadius: 4,
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
                alignItems: {
                  xs: "flex-start",
                  sm: "center",
                },
                justifyContent:
                  "space-between",
                gap: 2,
                flexDirection: {
                  xs: "column",
                  sm: "row",
                },
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
                    color: "#fff",
                    boxShadow:
                      "0 8px 20px rgba(52, 81, 209, 0.25)",
                    flexShrink: 0,
                  }}
                >
                  <TicketIcon size={28} />
                </Box>

                <Box>
                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 800,
                      color: "#0f172a",
                      fontSize: {
                        xs: "1.65rem",
                        md: "2rem",
                      },
                    }}
                  >
                    Tickets
                  </Typography>

                  <Typography
                    sx={{
                      color: "#64748b",
                      mt: 0.5,
                    }}
                  >
                    Search, filter and manage
                    support tickets
                  </Typography>
                </Box>
              </Box>

              <Button
                variant="outlined"
                startIcon={
                  sortOrder === "desc" ? (
                    <ArrowDownAZ size={18} />
                  ) : (
                    <ArrowUpAZ size={18} />
                  )
                }
                onClick={() =>
                  handleSortOrderChange(
                    sortOrder === "desc"
                      ? "asc"
                      : "desc",
                  )
                }
                sx={{
                  borderRadius: 2.5,
                  textTransform: "none",
                  fontWeight: 700,
                  borderColor: "#cbd5e1",
                  color: "#334155",
                  "&:hover": {
                    borderColor: "#3451d1",
                    color: "#3451d1",
                    backgroundColor: "#f5f7ff",
                  },
                }}
              >
                {sortOrder === "desc"
                  ? "Newest First"
                  : "Oldest First"}
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Summary Cards */}
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, 1fr)",
              md: "repeat(4, 1fr)",
            },
            gap: 2,
            mb: 3,
          }}
        >
          <Card
            sx={{
              borderRadius: 3,
              border:
                "1px solid rgba(52,81,209,0.10)",
              boxShadow:
                "0 6px 20px rgba(15,23,42,0.05)",
            }}
          >
            <CardContent sx={{ p: 2.2 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1.5,
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
                    backgroundColor: "#e9edff",
                    color: "#3451d1",
                  }}
                >
                  <ListFilter size={21} />
                </Box>

                <Box>
                  <Typography
                    variant="caption"
                    sx={{
                      color: "#64748b",
                      fontWeight: 600,
                    }}
                  >
                    Total Results
                  </Typography>

                  <Typography
                    sx={{
                      fontSize: "1.4rem",
                      fontWeight: 800,
                      color: "#0f172a",
                    }}
                  >
                    {total}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Card
            sx={{
              borderRadius: 3,
              border:
                "1px solid rgba(37,99,235,0.10)",
              boxShadow:
                "0 6px 20px rgba(15,23,42,0.05)",
            }}
          >
            <CardContent sx={{ p: 2.2 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1.5,
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
                    backgroundColor: "#eaf2ff",
                    color: "#2563eb",
                  }}
                >
                  <AlertCircle size={21} />
                </Box>

                <Box>
                  <Typography
                    variant="caption"
                    sx={{
                      color: "#64748b",
                      fontWeight: 600,
                    }}
                  >
                    Open
                  </Typography>

                  <Typography
                    sx={{
                      fontSize: "1.4rem",
                      fontWeight: 800,
                      color: "#0f172a",
                    }}
                  >
                    {openCount}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Card
            sx={{
              borderRadius: 3,
              border:
                "1px solid rgba(217,119,6,0.10)",
              boxShadow:
                "0 6px 20px rgba(15,23,42,0.05)",
            }}
          >
            <CardContent sx={{ p: 2.2 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1.5,
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
                    backgroundColor: "#fff7e6",
                    color: "#d97706",
                  }}
                >
                  <CalendarDays size={21} />
                </Box>

                <Box>
                  <Typography
                    variant="caption"
                    sx={{
                      color: "#64748b",
                      fontWeight: 600,
                    }}
                  >
                    In Progress
                  </Typography>

                  <Typography
                    sx={{
                      fontSize: "1.4rem",
                      fontWeight: 800,
                      color: "#0f172a",
                    }}
                  >
                    {inProgressCount}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Card
            sx={{
              borderRadius: 3,
              border:
                "1px solid rgba(220,38,38,0.10)",
              boxShadow:
                "0 6px 20px rgba(15,23,42,0.05)",
            }}
          >
            <CardContent sx={{ p: 2.2 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1.5,
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
                    backgroundColor: "#fff1f2",
                    color: "#dc2626",
                  }}
                >
                  <AlertCircle size={21} />
                </Box>

                <Box>
                  <Typography
                    variant="caption"
                    sx={{
                      color: "#64748b",
                      fontWeight: 600,
                    }}
                  >
                    Overdue
                  </Typography>

                  <Typography
                    sx={{
                      fontSize: "1.4rem",
                      fontWeight: 800,
                      color: "#0f172a",
                    }}
                  >
                    {overdueCount}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Error */}
        {error && (
          <Alert
            severity="error"
            sx={{
              mb: 3,
              borderRadius: 3,
            }}
            onClose={() => setError("")}
          >
            {error}
          </Alert>
        )}

        {/* Active Filter */}
        {hasFilters && (
          <Alert
            severity="info"
            icon={<Filter size={20} />}
            sx={{
              mb: 3,
              borderRadius: 3,
              border:
                "1px solid #bfdbfe",
            }}
            action={
              <Button
                color="inherit"
                size="small"
                startIcon={<X size={16} />}
                onClick={
                  handleResetFilters
                }
                sx={{
                  textTransform: "none",
                  fontWeight: 700,
                }}
              >
                Clear
              </Button>
            }
          >
            Showing filtered tickets.
          </Alert>
        )}

        {/* Filters */}
        <Card
          sx={{
            mb: 3,
            borderRadius: 4,
            border:
              "1px solid rgba(15,23,42,0.07)",
            boxShadow:
              "0 8px 30px rgba(15,23,42,0.06)",
          }}
        >
          <CardContent
            sx={{
              p: {
                xs: 2,
                md: 3,
              },
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1.2,
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
                  backgroundColor: "#e9edff",
                  color: "#3451d1",
                }}
              >
                <Filter size={21} />
              </Box>

              <Box>
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 800,
                    color: "#0f172a",
                  }}
                >
                  Filters & Search
                </Typography>

                <Typography
                  variant="body2"
                  sx={{
                    color: "#64748b",
                  }}
                >
                  Find exactly the tickets
                  you need
                </Typography>
              </Box>
            </Box>

            {/* Search */}
            <Box
              sx={{
                display: "flex",
                gap: 1.5,
                flexDirection: {
                  xs: "column",
                  sm: "row",
                },
                mb: 2,
              }}
            >
              <TextField
                fullWidth
                label="Search tickets"
                placeholder="Ticket number, title or description"
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    handleSearch();
                  }
                }}
                sx={{
                  "& .MuiOutlinedInput-root": {
                    borderRadius: 2.5,
                  },
                }}
              />

              <Button
                variant="contained"
                startIcon={<Search size={18} />}
                onClick={handleSearch}
                sx={{
                  minWidth: {
                    xs: "100%",
                    sm: 130,
                  },
                  borderRadius: 2.5,
                  textTransform: "none",
                  fontWeight: 700,
                  background:
                    "linear-gradient(135deg, #3451d1, #4f65dd)",
                  boxShadow:
                    "0 6px 15px rgba(52,81,209,0.22)",
                  "&:hover": {
                    background:
                      "linear-gradient(135deg, #2944b8, #465bd0)",
                  },
                }}
              >
                Search
              </Button>
            </Box>

            {/* Filter Row */}
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: {
                  xs: "1fr",
                  sm: "repeat(2, 1fr)",
                  lg: "repeat(5, 1fr)",
                },
                gap: 1.5,
              }}
            >
              <FormControl fullWidth>
                <InputLabel>
                  Status
                </InputLabel>

                <Select
                  value={status}
                  label="Status"
                  onChange={(event) =>
                    handleStatusChange(
                      event.target.value,
                    )
                  }
                  sx={{
                    borderRadius: 2.5,
                  }}
                >
                  {STATUS_OPTIONS.map(
                    (option) => (
                      <MenuItem
                        key={option.value}
                        value={option.value}
                      >
                        {option.label}
                      </MenuItem>
                    ),
                  )}
                </Select>
              </FormControl>

              <FormControl fullWidth>
                <InputLabel>
                  Priority
                </InputLabel>

                <Select
                  value={priority}
                  label="Priority"
                  onChange={(event) =>
                    handlePriorityChange(
                      event.target.value,
                    )
                  }
                  sx={{
                    borderRadius: 2.5,
                  }}
                >
                  {PRIORITY_OPTIONS.map(
                    (option) => (
                      <MenuItem
                        key={option.value}
                        value={option.value}
                      >
                        {option.label}
                      </MenuItem>
                    ),
                  )}
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Category ID"
                type="number"
                value={categoryId}
                onChange={(event) =>
                  handleCategoryChange(
                    event.target.value,
                  )
                }
                sx={{
                  "& .MuiOutlinedInput-root": {
                    borderRadius: 2.5,
                  },
                }}
              />

              <TextField
                fullWidth
                label="Assigned Agent ID"
                type="number"
                value={assignedAgentId}
                onChange={(event) =>
                  handleAgentChange(
                    event.target.value,
                  )
                }
                sx={{
                  "& .MuiOutlinedInput-root": {
                    borderRadius: 2.5,
                  },
                }}
              />

              <TextField
                fullWidth
                label="Customer ID"
                type="number"
                value={customerId}
                onChange={(event) =>
                  handleCustomerChange(
                    event.target.value,
                  )
                }
                sx={{
                  "& .MuiOutlinedInput-root": {
                    borderRadius: 2.5,
                  },
                }}
              />
            </Box>

            {/* Sorting */}
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: {
                  xs: "1fr",
                  sm: "repeat(3, 1fr)",
                },
                gap: 1.5,
                mt: 2,
              }}
            >
              <FormControl fullWidth>
                <InputLabel>
                  Sort By
                </InputLabel>

                <Select
                  value={sortBy}
                  label="Sort By"
                  onChange={(event) =>
                    handleSortByChange(
                      event.target.value,
                    )
                  }
                  sx={{
                    borderRadius: 2.5,
                  }}
                >
                  {SORT_OPTIONS.map(
                    (option) => (
                      <MenuItem
                        key={option.value}
                        value={option.value}
                      >
                        {option.label}
                      </MenuItem>
                    ),
                  )}
                </Select>
              </FormControl>

              <FormControl fullWidth>
                <InputLabel>
                  Sort Order
                </InputLabel>

                <Select
                  value={sortOrder}
                  label="Sort Order"
                  onChange={(event) =>
                    handleSortOrderChange(
                      event.target.value,
                    )
                  }
                  sx={{
                    borderRadius: 2.5,
                  }}
                >
                  <MenuItem value="desc">
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1,
                      }}
                    >
                      <ArrowDownAZ size={18} />
                      Descending
                    </Box>
                  </MenuItem>

                  <MenuItem value="asc">
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1,
                      }}
                    >
                      <ArrowUpAZ size={18} />
                      Ascending
                    </Box>
                  </MenuItem>
                </Select>
              </FormControl>

              <Button
                variant="outlined"
                startIcon={<X size={18} />}
                onClick={handleResetFilters}
                sx={{
                  borderRadius: 2.5,
                  textTransform: "none",
                  fontWeight: 700,
                  borderColor: "#cbd5e1",
                  color: "#475569",
                  "&:hover": {
                    borderColor: "#3451d1",
                    color: "#3451d1",
                    backgroundColor:
                      "#f5f7ff",
                  },
                }}
              >
                Reset Filters
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Tickets Table */}
        <Card
          sx={{
            borderRadius: 4,
            overflow: "hidden",
            border:
              "1px solid rgba(15,23,42,0.07)",
            boxShadow:
              "0 10px 35px rgba(15,23,42,0.07)",
          }}
        >
          <Box
            sx={{
              px: {
                xs: 2,
                md: 3,
              },
              py: 2.2,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 2,
              borderBottom:
                "1px solid #e2e8f0",
            }}
          >
            <Box>
              <Typography
                sx={{
                  fontWeight: 800,
                  color: "#0f172a",
                  fontSize: "1.05rem",
                }}
              >
                All Tickets
              </Typography>

              <Typography
                variant="body2"
                sx={{
                  color: "#64748b",
                  mt: 0.3,
                }}
              >
                {total} ticket
                {total !== 1 ? "s" : ""} found
              </Typography>
            </Box>

            <Box
              sx={{
                width: 40,
                height: 40,
                borderRadius: 2.5,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "#e9edff",
                color: "#3451d1",
              }}
            >
              <TicketIcon size={20} />
            </Box>
          </Box>

          {loading ? (
            <Box
              sx={{
                minHeight: 360,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <CircularProgress />
            </Box>
          ) : (
            <>
              <TableContainer
                sx={{
                  overflowX: "auto",
                }}
              >
                <Table
                  sx={{
                    minWidth: 1050,
                  }}
                >
                  <TableHead>
                    <TableRow
                      sx={{
                        backgroundColor:
                          "#f8fafc",
                      }}
                    >
                      {[
                        "Ticket",
                        "Title",
                        "Customer",
                        "Agent",
                        "Category",
                        "Priority",
                        "Status",
                        "Due Date",
                        "Action",
                      ].map((heading) => (
                        <TableCell
                          key={heading}
                          sx={{
                            fontWeight: 800,
                            color: "#475569",
                            fontSize:
                              "0.78rem",
                            textTransform:
                              "uppercase",
                            letterSpacing:
                              "0.03em",
                            whiteSpace:
                              "nowrap",
                            borderBottom:
                              "1px solid #e2e8f0",
                          }}
                        >
                          {heading}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>

                  <TableBody>
                    {tickets.length === 0 ? (
                      <TableRow>
                        <TableCell
                          colSpan={9}
                          align="center"
                        >
                          <Box
                            sx={{
                              py: 8,
                              display: "flex",
                              flexDirection:
                                "column",
                              alignItems:
                                "center",
                              justifyContent:
                                "center",
                            }}
                          >
                            <Box
                              sx={{
                                width: 64,
                                height: 64,
                                borderRadius: 4,
                                display:
                                  "flex",
                                alignItems:
                                  "center",
                                justifyContent:
                                  "center",
                                backgroundColor:
                                  "#f1f5f9",
                                color:
                                  "#64748b",
                                mb: 2,
                              }}
                            >
                              <TicketIcon
                                size={30}
                              />
                            </Box>

                            <Typography
                              sx={{
                                fontWeight: 700,
                                color:
                                  "#334155",
                              }}
                            >
                              No tickets found
                            </Typography>

                            <Typography
                              variant="body2"
                              sx={{
                                color:
                                  "#64748b",
                                mt: 0.5,
                              }}
                            >
                              Try changing
                              your filters
                              or search
                              term.
                            </Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ) : (
                      tickets.map(
                        (ticket) => {
                          const statusStyles =
                            getStatusStyles(
                              ticket.status,
                            );

                          const priorityStyles =
                            getPriorityStyles(
                              ticket.priority,
                            );

                          const overdue =
                            isTicketOverdue(
                              ticket,
                            );

                          return (
                            <TableRow
                              key={ticket.id}
                              hover
                              sx={{
                                cursor:
                                  "pointer",
                                transition:
                                  "background-color 0.15s ease",
                                "&:hover":
                                  {
                                    backgroundColor:
                                      "#f8faff",
                                  },
                                "& td": {
                                  borderBottom:
                                    "1px solid #f1f5f9",
                                },
                              }}
                              onClick={() =>
                                navigate(
                                  `/tickets/${ticket.id}`,
                                )
                              }
                            >
                              <TableCell>
                                <Typography
                                  sx={{
                                    fontWeight: 800,
                                    color:
                                      "#3451d1",
                                    fontSize:
                                      "0.88rem",
                                    whiteSpace:
                                      "nowrap",
                                  }}
                                >
                                  {
                                    ticket.ticket_number
                                  }
                                </Typography>

                                <Typography
                                  variant="caption"
                                  sx={{
                                    color:
                                      "#94a3b8",
                                  }}
                                >
                                  #{ticket.id}
                                </Typography>
                              </TableCell>

                              <TableCell>
                                <Box
                                  sx={{
                                    maxWidth: 280,
                                  }}
                                >
                                  <Typography
                                    sx={{
                                      fontWeight: 700,
                                      color:
                                        "#1e293b",
                                      overflow:
                                        "hidden",
                                      textOverflow:
                                        "ellipsis",
                                      whiteSpace:
                                        "nowrap",
                                    }}
                                  >
                                    {
                                      ticket.title
                                    }
                                  </Typography>

                                  <Typography
                                    variant="caption"
                                    sx={{
                                      display:
                                        "block",
                                      mt: 0.4,
                                      color:
                                        "#94a3b8",
                                      overflow:
                                        "hidden",
                                      textOverflow:
                                        "ellipsis",
                                      whiteSpace:
                                        "nowrap",
                                    }}
                                  >
                                    {
                                      ticket.description
                                    }
                                  </Typography>
                                </Box>
                              </TableCell>

                              <TableCell>
                                <Box
                                  sx={{
                                    display:
                                      "flex",
                                    alignItems:
                                      "center",
                                    gap: 0.8,
                                    whiteSpace:
                                      "nowrap",
                                  }}
                                >
                                  <UserRound
                                    size={15}
                                    color="#64748b"
                                  />

                                  <Typography
                                    variant="body2"
                                    sx={{
                                      color:
                                        "#475569",
                                      fontWeight: 600,
                                    }}
                                  >
                                    #
                                    {
                                      ticket.customer_id
                                    }
                                  </Typography>
                                </Box>
                              </TableCell>

                              <TableCell>
                                <Typography
                                  variant="body2"
                                  sx={{
                                    color:
                                      ticket.assigned_agent_id
                                        ? "#475569"
                                        : "#94a3b8",
                                    fontWeight:
                                      ticket.assigned_agent_id
                                        ? 600
                                        : 500,
                                    whiteSpace:
                                      "nowrap",
                                  }}
                                >
                                  {ticket.assigned_agent_id
                                    ? `#${ticket.assigned_agent_id}`
                                    : "Unassigned"}
                                </Typography>
                              </TableCell>

                              <TableCell>
                                <Chip
                                  label={`#${ticket.category_id}`}
                                  size="small"
                                  sx={{
                                    fontWeight: 700,
                                    backgroundColor:
                                      "#f1f5f9",
                                    color:
                                      "#475569",
                                    border:
                                      "1px solid #e2e8f0",
                                  }}
                                />
                              </TableCell>

                              <TableCell>
                                <Chip
                                  label={
                                    ticket.priority
                                  }
                                  size="small"
                                  sx={{
                                    fontWeight: 800,
                                    backgroundColor:
                                      priorityStyles.background,
                                    color:
                                      priorityStyles.color,
                                    border: `1px solid ${priorityStyles.border}`,
                                  }}
                                />
                              </TableCell>

                              <TableCell>
                                <Chip
                                  label={formatStatus(
                                    ticket.status,
                                  )}
                                  size="small"
                                  sx={{
                                    fontWeight: 800,
                                    backgroundColor:
                                      statusStyles.background,
                                    color:
                                      statusStyles.color,
                                    border: `1px solid ${statusStyles.border}`,
                                  }}
                                />
                              </TableCell>

                              <TableCell>
                                <Box>
                                  <Typography
                                    variant="body2"
                                    sx={{
                                      color:
                                        overdue
                                          ? "#dc2626"
                                          : "#475569",
                                      fontWeight:
                                        overdue
                                          ? 800
                                          : 600,
                                      whiteSpace:
                                        "nowrap",
                                    }}
                                  >
                                    {formatDate(
                                      ticket.due_date,
                                    )}
                                  </Typography>

                                  {overdue && (
                                    <Typography
                                      variant="caption"
                                      sx={{
                                        color:
                                          "#dc2626",
                                        fontWeight:
                                          700,
                                      }}
                                    >
                                      Overdue
                                    </Typography>
                                  )}
                                </Box>
                              </TableCell>

                              <TableCell
                                onClick={(event) =>
                                  event.stopPropagation()
                                }
                              >
                                <Button
                                  variant="outlined"
                                  size="small"
                                  endIcon={
                                    <ChevronRight
                                      size={16}
                                    />
                                  }
                                  onClick={() =>
                                    navigate(
                                      `/tickets/${ticket.id}`,
                                    )
                                  }
                                  sx={{
                                    borderRadius: 2,
                                    textTransform:
                                      "none",
                                    fontWeight: 700,
                                    whiteSpace:
                                      "nowrap",
                                    borderColor:
                                      "#cbd5e1",
                                    color:
                                      "#3451d1",
                                    "&:hover":
                                      {
                                        borderColor:
                                          "#3451d1",
                                        backgroundColor:
                                          "#f5f7ff",
                                      },
                                  }}
                                >
                                  View
                                </Button>
                              </TableCell>
                            </TableRow>
                          );
                        },
                      )
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              <TablePagination
                component="div"
                count={total}
                page={Math.max(
                  page - 1,
                  0,
                )}
                onPageChange={
                  handlePageChange
                }
                rowsPerPage={pageSize}
                onRowsPerPageChange={
                  handleRowsPerPageChange
                }
                rowsPerPageOptions={[
                  10,
                  20,
                  50,
                  100,
                ]}
                sx={{
                  borderTop:
                    "1px solid #e2e8f0",
                  "& .MuiTablePagination-toolbar":
                    {
                      minHeight: 58,
                    },
                }}
              />
            </>
          )}
        </Card>

        {/* Footer */}
        <Box
          sx={{
            mt: 2,
            display: "flex",
            justifyContent:
              "space-between",
            alignItems: "center",
            gap: 1,
            flexWrap: "wrap",
          }}
        >
          <Typography
            variant="caption"
            sx={{
              color: "#94a3b8",
            }}
          >
            Logged in as{" "}
            <strong>{user?.name}</strong>{" "}
            ({user?.role})
          </Typography>

          <Typography
            variant="caption"
            sx={{
              color: "#94a3b8",
            }}
          >
            Showing {tickets.length} of{" "}
            {total} tickets
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}