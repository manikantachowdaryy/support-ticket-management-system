import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
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

interface Comment {
  id: number;
  ticket_id: number;
  user_id: number;
  comment: string;
  created_at: string;
  updated_at: string;
}

interface Attachment {
  id: number;
  ticket_id: number;
  uploaded_by: number;
  original_filename: string;
  file_type: string;
  file_size: number;
  storage_path?: string;
  created_at: string;
}

interface StatusHistory {
  id: number;
  ticket_id: number;
  old_status: string;
  new_status: string;
  changed_by: number;
  created_at: string;
}

interface UserOption {
  id: number;
  name: string;
  email?: string;
  role: string;
  is_active: boolean;
}

const STATUS_TRANSITIONS: Record<string, string[]> = {
  OPEN: ["IN_PROGRESS"],
  IN_PROGRESS: ["RESOLVED", "OPEN"],
  RESOLVED: ["CLOSED", "OPEN"],
  CLOSED: [],
};

function formatStatus(value: string) {
  return value.replaceAll("_", " ");
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (error.response?.status === 401) {
      return "Your session has expired. Please log in again.";
    }

    if (error.response?.status === 403) {
      return "You do not have permission to perform this action.";
    }

    if (error.response?.status === 404) {
      return "The requested resource was not found.";
    }

    return error.message || "Something went wrong.";
  }

  return "Something went wrong.";
}

function getStatusColor(
  status: string,
): "default" | "warning" | "info" | "success" {
  switch (status) {
    case "OPEN":
      return "warning";
    case "IN_PROGRESS":
      return "info";
    case "RESOLVED":
      return "success";
    default:
      return "default";
  }
}

function getPriorityColor(
  priority: string,
): "default" | "warning" | "error" {
  switch (priority) {
    case "CRITICAL":
      return "error";
    case "HIGH":
      return "warning";
    default:
      return "default";
  }
}

export default function TicketDetails() {
  const { ticketId } = useParams<{ ticketId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [history, setHistory] = useState<StatusHistory[]>([]);
  const [agents, setAgents] = useState<UserOption[]>([]);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [selectedStatus, setSelectedStatus] = useState("");
  const [selectedAgent, setSelectedAgent] = useState("");

  const [newComment, setNewComment] = useState("");

  const [editingCommentId, setEditingCommentId] =
    useState<number | null>(null);

  const [editingCommentText, setEditingCommentText] =
    useState("");

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const isAdmin = user?.role === "ADMIN";
  const isAgent = user?.role === "SUPPORT_AGENT";
  const isCustomer = user?.role === "CUSTOMER";

  const canManageTicket = isAdmin || isAgent;
  const isClosed = ticket?.status === "CLOSED";

  const canChangeStatus =
    canManageTicket &&
    !isClosed &&
    Boolean(ticket) &&
    (isAdmin || ticket?.assigned_agent_id === user?.id);

  const canAssign = canManageTicket && !isClosed;

  const loadTicketDetails = useCallback(async () => {
    if (!ticketId) {
      setError("Ticket ID is missing.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const [
        ticketResponse,
        commentsResponse,
        attachmentsResponse,
        historyResponse,
      ] = await Promise.all([
        api.get<Ticket>(`/tickets/${ticketId}`),
        api.get<Comment[]>(`/tickets/${ticketId}/comments`),
        api.get<Attachment[]>(
          `/tickets/${ticketId}/attachments`,
        ),
        api.get<StatusHistory[]>(
          `/tickets/${ticketId}/status-history`,
        ),
      ]);

      const loadedTicket = ticketResponse.data;

      setTicket(loadedTicket);
      setComments(commentsResponse.data);
      setAttachments(attachmentsResponse.data);
      setHistory(historyResponse.data);

      setSelectedAgent(
        loadedTicket.assigned_agent_id?.toString() ?? "",
      );

      setSelectedStatus("");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    void loadTicketDetails();
  }, [loadTicketDetails]);

  useEffect(() => {
    if (!isAdmin) {
      return;
    }

    const loadAgents = async () => {
      try {
        const response = await api.get<unknown>("/users");

        const data = response.data;

        let users: UserOption[] = [];

        if (Array.isArray(data)) {
          users = data as UserOption[];
        } else if (
          data &&
          typeof data === "object" &&
          "items" in data &&
          Array.isArray(data.items)
        ) {
          users = data.items as UserOption[];
        }

        setAgents(
          users.filter(
            (item) =>
              item.role === "SUPPORT_AGENT" &&
              item.is_active,
          ),
        );
      } catch {
        // Agent ID input remains available if the user
        // list endpoint is not available.
      }
    };

    void loadAgents();
  }, [isAdmin]);

  const runAction = async (
    action: () => Promise<unknown>,
    successMessage: string,
  ) => {
    setBusy(true);
    setError("");
    setSuccess("");

    try {
      await action();
      await loadTicketDetails();
      setSuccess(successMessage);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const handleStatusChange = () => {
    if (!ticket || !selectedStatus) {
      return;
    }

    void runAction(
      () =>
        api.patch(`/tickets/${ticket.id}/status`, {
          status: selectedStatus,
        }),
      "Ticket status updated successfully.",
    );
  };

  const handleAssignment = () => {
    if (!ticket || !selectedAgent.trim()) {
      return;
    }

    const agentId = Number(selectedAgent);

    if (!Number.isInteger(agentId) || agentId <= 0) {
      setError("Please enter a valid support agent ID.");
      return;
    }

    void runAction(
      () =>
        api.patch(`/tickets/${ticket.id}/assign`, {
          agent_id: agentId,
        }),
      "Ticket assignment updated successfully.",
    );
  };

  const handleAddComment = () => {
    if (!ticket || !newComment.trim()) {
      return;
    }

    void runAction(
      async () => {
        await api.post(`/tickets/${ticket.id}/comments`, {
          comment: newComment.trim(),
        });

        setNewComment("");
      },
      "Comment added successfully.",
    );
  };

  const handleUpdateComment = (commentId: number) => {
    if (!editingCommentText.trim()) {
      return;
    }

    void runAction(
      async () => {
        await api.put(`/tickets/comments/${commentId}`, {
          comment: editingCommentText.trim(),
        });

        setEditingCommentId(null);
        setEditingCommentText("");
      },
      "Comment updated successfully.",
    );
  };

  const handleDeleteComment = (commentId: number) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this comment?",
    );

    if (!confirmed) {
      return;
    }

    void runAction(
      () => api.delete(`/tickets/comments/${commentId}`),
      "Comment deleted successfully.",
    );
  };

  const handleUploadAttachment = () => {
    if (!ticket || !selectedFile) {
      return;
    }

    void runAction(
      async () => {
        const formData = new FormData();

        formData.append("file", selectedFile);

        await api.post(
          `/tickets/${ticket.id}/attachments`,
          formData,
        );

        setSelectedFile(null);
      },
      "Attachment uploaded successfully.",
    );
  };

  const handleDownloadAttachment = async (
    attachment: Attachment,
  ) => {
    setError("");

    try {
      const response = await api.get(
        `/tickets/attachments/${attachment.id}/download`,
        {
          responseType: "blob",
        },
      );

      const url = URL.createObjectURL(response.data);

      const link = document.createElement("a");

      link.href = url;
      link.download = attachment.original_filename;

      document.body.appendChild(link);
      link.click();
      link.remove();

      URL.revokeObjectURL(url);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleDeleteAttachment = (
    attachmentId: number,
  ) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this attachment?",
    );

    if (!confirmed) {
      return;
    }

    void runAction(
      () =>
        api.delete(
          `/tickets/attachments/${attachmentId}`,
        ),
      "Attachment deleted successfully.",
    );
  };

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: "70vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!ticket) {
    return (
      <Box sx={{ p: { xs: 2, md: 4 } }}>
        <Alert severity="error">
          {error || "Ticket not found."}
        </Alert>

        <Button
          sx={{ mt: 2 }}
          variant="outlined"
          onClick={() => navigate("/tickets")}
        >
          Back to Tickets
        </Button>
      </Box>
    );
  }

  const availableStatuses =
    STATUS_TRANSITIONS[ticket.status] ?? [];

  return (
    <Box
      sx={{
        p: { xs: 2, md: 4 },
        maxWidth: 1100,
        mx: "auto",
      }}
    >
      <Button
        variant="text"
        onClick={() => navigate("/tickets")}
        sx={{ mb: 2 }}
      >
        ← Back to Tickets
      </Button>

      <Typography
        variant="h4"
        sx={{
          fontWeight: 700,
          mb: 0.5,
        }}
      >
        Ticket Details
      </Typography>

      <Typography
        color="text.secondary"
        sx={{ mb: 3 }}
      >
        {ticket.ticket_number}
      </Typography>

      {error && (
        <Alert
          severity="error"
          sx={{ mb: 2 }}
          onClose={() => setError("")}
        >
          {error}
        </Alert>
      )}

      {success && (
        <Alert
          severity="success"
          sx={{ mb: 2 }}
          onClose={() => setSuccess("")}
        >
          {success}
        </Alert>
      )}

      <Stack spacing={3}>
        {/* Ticket Information */}
        <Card>
          <CardContent>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                mb: 2,
              }}
            >
              Ticket Information
            </Typography>

            <Typography
              variant="h5"
              sx={{
                fontWeight: 600,
                mb: 1,
              }}
            >
              {ticket.title}
            </Typography>

            <Typography
              sx={{
                whiteSpace: "pre-wrap",
                mb: 3,
              }}
            >
              {ticket.description}
            </Typography>

            <Stack
              direction="row"
              spacing={1}
              useFlexGap
              sx={{
                flexWrap: "wrap",
                mb: 3,
              }}
            >
              <Chip
                label={formatStatus(ticket.status)}
                color={getStatusColor(ticket.status)}
              />

              <Chip
                label={ticket.priority}
                color={getPriorityColor(ticket.priority)}
              />
            </Stack>

            <Divider sx={{ mb: 2 }} />

            <Stack spacing={1}>
              <Typography>
                <strong>Ticket ID:</strong> {ticket.id}
              </Typography>

              <Typography>
                <strong>Customer ID:</strong>{" "}
                {ticket.customer_id}
              </Typography>

              <Typography>
                <strong>Assigned Agent:</strong>{" "}
                {ticket.assigned_agent_id ?? "Unassigned"}
              </Typography>

              <Typography>
                <strong>Category ID:</strong>{" "}
                {ticket.category_id}
              </Typography>

              <Typography>
                <strong>Created:</strong>{" "}
                {formatDate(ticket.created_at)}
              </Typography>

              <Typography>
                <strong>Updated:</strong>{" "}
                {formatDate(ticket.updated_at)}
              </Typography>

              <Typography>
                <strong>Due Date:</strong>{" "}
                {formatDate(ticket.due_date)}
              </Typography>
            </Stack>
          </CardContent>
        </Card>

        {/* Status */}
        {canChangeStatus &&
          availableStatuses.length > 0 && (
            <Card>
              <CardContent>
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 700,
                    mb: 2,
                  }}
                >
                  Change Status
                </Typography>

                <Stack spacing={2}>
                  <TextField
                    select
                    fullWidth
                    label="New Status"
                    value={selectedStatus}
                    onChange={(event) =>
                      setSelectedStatus(event.target.value)
                    }
                  >
                    {availableStatuses.map((status) => (
                      <MenuItem
                        key={status}
                        value={status}
                      >
                        {formatStatus(status)}
                      </MenuItem>
                    ))}
                  </TextField>

                  <Button
                    variant="contained"
                    disabled={
                      busy || !selectedStatus
                    }
                    onClick={handleStatusChange}
                  >
                    Update Status
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          )}

        {/* Assignment */}
        {canAssign && (
          <Card>
            <CardContent>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  mb: 2,
                }}
              >
                Assign / Reassign Ticket
              </Typography>

              <Stack spacing={2}>
                {isAdmin && agents.length > 0 ? (
                  <TextField
                    select
                    fullWidth
                    label="Support Agent"
                    value={selectedAgent}
                    onChange={(event) =>
                      setSelectedAgent(
                        event.target.value,
                      )
                    }
                  >
                    {agents.map((agent) => (
                      <MenuItem
                        key={agent.id}
                        value={String(agent.id)}
                      >
                        {agent.name} — ID {agent.id}
                      </MenuItem>
                    ))}
                  </TextField>
                ) : (
                  <TextField
                    fullWidth
                    type="number"
                    label="Support Agent ID"
                    value={selectedAgent}
                    onChange={(event) =>
                      setSelectedAgent(
                        event.target.value,
                      )
                    }
                    helperText="Enter the ID of an active support agent."
                  />
                )}

                <Button
                  variant="contained"
                  disabled={
                    busy || !selectedAgent
                  }
                  onClick={handleAssignment}
                >
                  Save Assignment
                </Button>
              </Stack>
            </CardContent>
          </Card>
        )}

        {/* Comments */}
        <Card>
          <CardContent>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                mb: 2,
              }}
            >
              Comments ({comments.length})
            </Typography>

            <Stack spacing={2}>
              {comments.length === 0 && (
                <Typography color="text.secondary">
                  No comments yet.
                </Typography>
              )}

              {comments.map((comment) => {
                const canEdit =
                  !isClosed &&
                  (isAdmin ||
                    comment.user_id === user?.id);

                const isEditing =
                  editingCommentId === comment.id;

                return (
                  <Box
                    key={comment.id}
                    sx={{
                      border: "1px solid",
                      borderColor: "divider",
                      borderRadius: 2,
                      p: 2,
                    }}
                  >
                    <Typography
                      variant="caption"
                      color="text.secondary"
                    >
                      User #{comment.user_id} •{" "}
                      {formatDate(comment.created_at)}
                    </Typography>

                    {isEditing ? (
                      <Stack
                        spacing={1}
                        sx={{ mt: 1 }}
                      >
                        <TextField
                          multiline
                          minRows={3}
                          fullWidth
                          value={editingCommentText}
                          onChange={(event) =>
                            setEditingCommentText(
                              event.target.value,
                            )
                          }
                          slotProps={{
                            htmlInput: {
                              maxLength: 5000,
                            },
                          }}
                        />

                        <Stack
                          direction="row"
                          spacing={1}
                        >
                          <Button
                            variant="contained"
                            disabled={
                              busy ||
                              !editingCommentText.trim()
                            }
                            onClick={() =>
                              handleUpdateComment(
                                comment.id,
                              )
                            }
                          >
                            Save
                          </Button>

                          <Button
                            onClick={() => {
                              setEditingCommentId(null);
                              setEditingCommentText("");
                            }}
                          >
                            Cancel
                          </Button>
                        </Stack>
                      </Stack>
                    ) : (
                      <>
                        <Typography
                          sx={{
                            mt: 1,
                            whiteSpace: "pre-wrap",
                          }}
                        >
                          {comment.comment}
                        </Typography>

                        {canEdit && (
                          <Stack
                            direction="row"
                            spacing={1}
                            sx={{ mt: 1 }}
                          >
                            <Button
                              size="small"
                              onClick={() => {
                                setEditingCommentId(
                                  comment.id,
                                );
                                setEditingCommentText(
                                  comment.comment,
                                );
                              }}
                            >
                              Edit
                            </Button>

                            <Button
                              size="small"
                              color="error"
                              disabled={busy}
                              onClick={() =>
                                handleDeleteComment(
                                  comment.id,
                                )
                              }
                            >
                              Delete
                            </Button>
                          </Stack>
                        )}
                      </>
                    )}
                  </Box>
                );
              })}

              {!isClosed && (
                <>
                  <Divider />

                  <TextField
                    fullWidth
                    multiline
                    minRows={3}
                    label="Add Comment"
                    value={newComment}
                    onChange={(event) =>
                      setNewComment(event.target.value)
                    }
                    slotProps={{
                      htmlInput: {
                        maxLength: 5000,
                      },
                    }}
                  />

                  <Button
                    variant="contained"
                    disabled={
                      busy || !newComment.trim()
                    }
                    onClick={handleAddComment}
                  >
                    Add Comment
                  </Button>
                </>
              )}

              {isClosed && (
                <Alert severity="info">
                  Closed tickets cannot receive new
                  comments.
                </Alert>
              )}
            </Stack>
          </CardContent>
        </Card>

        {/* Attachments */}
        <Card>
          <CardContent>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                mb: 2,
              }}
            >
              Attachments ({attachments.length})
            </Typography>

            <Stack spacing={2}>
              {attachments.length === 0 && (
                <Typography color="text.secondary">
                  No attachments uploaded.
                </Typography>
              )}

              {attachments.map((attachment) => (
                <Box
                  key={attachment.id}
                  sx={{
                    border: "1px solid",
                    borderColor: "divider",
                    borderRadius: 2,
                    p: 2,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 2,
                    flexWrap: "wrap",
                  }}
                >
                  <Box sx={{ minWidth: 0 }}>
                    <Typography
                      sx={{
                        overflowWrap: "anywhere",
                      }}
                    >
                      {attachment.original_filename}
                    </Typography>

                    <Typography
                      variant="caption"
                      color="text.secondary"
                    >
                      {formatFileSize(
                        attachment.file_size,
                      )}{" "}
                      • Uploaded by User #
                      {attachment.uploaded_by}
                    </Typography>
                  </Box>

                  <Stack
                    direction="row"
                    spacing={1}
                  >
                    <Button
                      size="small"
                      onClick={() =>
                        void handleDownloadAttachment(
                          attachment,
                        )
                      }
                    >
                      Download
                    </Button>

                    {!isClosed &&
                      (isAdmin ||
                        attachment.uploaded_by ===
                          user?.id) && (
                        <Button
                          size="small"
                          color="error"
                          disabled={busy}
                          onClick={() =>
                            handleDeleteAttachment(
                              attachment.id,
                            )
                          }
                        >
                          Delete
                        </Button>
                      )}
                  </Stack>
                </Box>
              ))}

              {!isClosed && (
                <>
                  <Divider />

                  <Button
                    variant="outlined"
                    component="label"
                    disabled={busy}
                  >
                    Choose File

                    <input
                      type="file"
                      hidden
                      onChange={(event) =>
                        setSelectedFile(
                          event.target.files?.[0] ??
                            null,
                        )
                      }
                    />
                  </Button>

                  {selectedFile && (
                    <Typography variant="body2">
                      Selected: {selectedFile.name}
                    </Typography>
                  )}

                  <Button
                    variant="contained"
                    disabled={
                      busy || !selectedFile
                    }
                    onClick={handleUploadAttachment}
                  >
                    Upload Attachment
                  </Button>
                </>
              )}
            </Stack>
          </CardContent>
        </Card>

        {/* Status History */}
        <Card>
          <CardContent>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                mb: 2,
              }}
            >
              Status History
            </Typography>

            <Stack spacing={2}>
              {history.length === 0 && (
                <Typography color="text.secondary">
                  No status changes recorded.
                </Typography>
              )}

              {history.map((item) => (
                <Box
                  key={item.id}
                  sx={{
                    p: 2,
                    borderLeft: "3px solid",
                    borderColor: "primary.main",
                    backgroundColor: "action.hover",
                    borderRadius: 1,
                  }}
                >
                  <Typography
                    sx={{ fontWeight: 600 }}
                  >
                    {formatStatus(item.old_status)}
                    {" → "}
                    {formatStatus(item.new_status)}
                  </Typography>

                  <Typography
                    variant="caption"
                    color="text.secondary"
                  >
                    Changed by User #
                    {item.changed_by} •{" "}
                    {formatDate(item.created_at)}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Stack>

      {busy && (
        <Box
          sx={{
            position: "fixed",
            bottom: 20,
            right: 20,
          }}
        >
          <CircularProgress size={28} />
        </Box>
      )}

      {isCustomer && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            display: "block",
            mt: 3,
          }}
        >
          Status changes and ticket assignments are managed
          by support staff.
        </Typography>
      )}
    </Box>
  );
}