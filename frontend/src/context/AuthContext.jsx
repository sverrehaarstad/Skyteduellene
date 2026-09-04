import { createContext, useContext, useEffect, useState, useCallback } from "react";
import api from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null = loading, false = anon, obj = user
  const [token, setToken] = useState(localStorage.getItem("rt_token"));

  const refreshMe = useCallback(async () => {
    if (!localStorage.getItem("rt_token")) {
      setUser(false);
      return;
    }
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch {
      localStorage.removeItem("rt_token");
      setToken(null);
      setUser(false);
    }
  }, []);

  useEffect(() => {
    refreshMe();
  }, [refreshMe]);

  const setSession = (data) => {
    localStorage.setItem("rt_token", data.token);
    setToken(data.token);
    setUser(data.user);
  };

  const logout = () => {
    localStorage.removeItem("rt_token");
    setToken(null);
    setUser(false);
  };

  return (
    <AuthContext.Provider value={{ user, token, setSession, logout, refreshMe, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
