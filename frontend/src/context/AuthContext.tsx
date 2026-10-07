import {
    createContext,
    useContext,
    useEffect,
    useState,
    type ReactNode,
  } from "react";
  
  import { api } from "../api/axios";
  import type {
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    User,
  } from "../types/auth";
  
  interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (credentials: LoginRequest) => Promise<void>;
    register: (data: RegisterRequest) => Promise<void>;
    logout: () => Promise<void>;
    refreshUser: () => Promise<void>;
  }
  
  const AuthContext = createContext<AuthContextType | undefined>(undefined);
  
  interface AuthProviderProps {
    children: ReactNode;
  }
  
  export function AuthProvider({ children }: AuthProviderProps) {
    const [user, setUser] = useState<User | null>(() => {
      const storedUser = localStorage.getItem("current_user");
  
      if (!storedUser) {
        return null;
      }
  
      try {
        return JSON.parse(storedUser) as User;
      } catch {
        localStorage.removeItem("current_user");
        return null;
      }
    });
  
    const [loading, setLoading] = useState(true);
  
    const saveSession = (tokens: TokenResponse) => {
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
    };
  
    const saveUser = (currentUser: User) => {
      setUser(currentUser);
      localStorage.setItem("current_user", JSON.stringify(currentUser));
    };
  
    const clearSession = () => {
      setUser(null);
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("current_user");
    };
  
    const refreshUser = async () => {
      try {
        const response = await api.get<User>("/auth/me");
        saveUser(response.data);
      } catch {
        clearSession();
      }
    };
  
    const login = async (credentials: LoginRequest) => {
      const response = await api.post<TokenResponse>(
        "/auth/login",
        credentials,
      );
  
      saveSession(response.data);
  
      const userResponse = await api.get<User>("/auth/me");
  
      saveUser(userResponse.data);
    };
  
    const register = async (data: RegisterRequest) => {
      await api.post("/auth/register", data);
    };
  
    const logout = async () => {
      const refreshToken = localStorage.getItem("refresh_token");
  
      try {
        if (refreshToken) {
          await api.post("/auth/logout", {
            refresh_token: refreshToken,
          });
        }
      } finally {
        clearSession();
      }
    };
  
    useEffect(() => {
      const initializeAuth = async () => {
        const accessToken = localStorage.getItem("access_token");
  
        if (accessToken) {
          await refreshUser();
        }
  
        setLoading(false);
      };
  
      initializeAuth();
    }, []);
  
    return (
      <AuthContext.Provider
        value={{
          user,
          loading,
          login,
          register,
          logout,
          refreshUser,
        }}
      >
        {children}
      </AuthContext.Provider>
    );
  }
  
  export function useAuth() {
    const context = useContext(AuthContext);
  
    if (!context) {
      throw new Error("useAuth must be used inside AuthProvider");
    }
  
    return context;
  }