import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, setAuthToken } from "../api";

const AuthContext = createContext(null);
const AUTH_TOKEN_KEY = "msp_platform_auth_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(AUTH_TOKEN_KEY));
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setAuthToken(token);
    if (!token) {
      setMe(null);
      setLoading(false);
      return;
    }
    api
      .get("/auth/me")
      .then((response) => setMe(response.data))
      .catch(() => {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        setToken(null);
        setMe(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const login = async (tenantSlug, email, password) => {
    const response = await api.post("/auth/login", {
      tenant_slug: tenantSlug,
      email,
      password,
    });
    const nextToken = response.data.access_token;
    localStorage.setItem(AUTH_TOKEN_KEY, nextToken);
    setToken(nextToken);
    setAuthToken(nextToken);
    const meResponse = await api.get("/auth/me");
    setMe(meResponse.data);
  };

  const logout = () => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    setToken(null);
    setMe(null);
    setAuthToken(null);
  };

  const value = useMemo(
    () => ({
      token,
      me,
      loading,
      login,
      logout,
      isAuthenticated: Boolean(token && me),
    }),
    [token, me, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return ctx;
}

