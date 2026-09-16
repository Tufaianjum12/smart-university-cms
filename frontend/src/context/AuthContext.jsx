import { createContext, useContext, useEffect, useState } from "react";
import apiClient from "../services/apiClient";

const AuthContext = createContext(null);
const TOKEN_KEY = "scms_access_token";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const expired = () => setUser(null);
    window.addEventListener("auth-expired", expired);
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) { setLoading(false); return () => window.removeEventListener("auth-expired", expired); }
    apiClient.get("/api/v1/auth/me").then(r => setUser(r.data)).catch(() => localStorage.removeItem(TOKEN_KEY)).finally(() => setLoading(false));
    return () => window.removeEventListener("auth-expired", expired);
  }, []);

  const login = async (email, password) => {
    const { data } = await apiClient.post("/api/v1/auth/login", { email, password });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    const me = await apiClient.get("/api/v1/auth/me");
    setUser(me.data);
    return me.data;
  };
  const logout = () => { localStorage.removeItem(TOKEN_KEY); setUser(null); };
  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}
export const useAuth = () => useContext(AuthContext);
export { TOKEN_KEY };
