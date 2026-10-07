import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    CircularProgress,
    TextField,
    Typography,
  } from "@mui/material";
  import { useState, type FormEvent } from "react";
  import { Link, useNavigate } from "react-router-dom";
  
  import { useAuth } from "../context/AuthContext";
  
  export default function Login() {
    const navigate = useNavigate();
    const { login } = useAuth();
  
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
  
    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
  
      setError("");
      setLoading(true);
  
      try {
        await login({
          email,
          password,
        });
  
        navigate("/dashboard");
      } catch (err: any) {
        const message =
          err.response?.data?.detail ??
          err.response?.data?.error?.message ??
          "Invalid email or password.";
  
        setError(message);
      } finally {
        setLoading(false);
      }
    };
  
    return (
      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          px: 2,
          background:
            "linear-gradient(135deg, #eef2ff 0%, #f8fafc 50%, #e8edff 100%)",
        }}
      >
        <Card
          sx={{
            width: "100%",
            maxWidth: 430,
            borderRadius: 3,
            boxShadow: "0 20px 60px rgba(15, 23, 42, 0.12)",
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                textAlign: "center",
              }}
              gutterBottom
            >
              SupportDesk
            </Typography>
  
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                textAlign: "center",
                mb: 4,
              }}
            >
              Sign in to manage your support tickets
            </Typography>
  
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
  
            <Box component="form" onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                margin="normal"
                required
                autoComplete="email"
              />
  
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                margin="normal"
                required
                autoComplete="current-password"
              />
  
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={loading}
                sx={{
                  mt: 3,
                  py: 1.4,
                  borderRadius: 2,
                  textTransform: "none",
                  fontSize: "1rem",
                  fontWeight: 600,
                }}
              >
                {loading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  "Sign In"
                )}
              </Button>
            </Box>
  
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                textAlign: "center",
                mt: 3,
              }}
            >
              Don't have an account?{" "}
              <Link
                to="/register"
                style={{
                  color: "#3451d1",
                  fontWeight: 600,
                  textDecoration: "none",
                }}
              >
                Create account
              </Link>
            </Typography>
          </CardContent>
        </Card>
      </Box>
    );
  }