// src/context/AuthContext.tsx
import { createContext, useContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import dayjs from "dayjs";
import API from "../api/axios";
import type { UsuarioPerfil } from "../api/usuarios";

interface AuthContextType {
  user: UsuarioPerfil | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const navigate = useNavigate();
  const [user, setUser] = useState<UsuarioPerfil | null>(null);
  const [init, setInit] = useState(true);

  useEffect(() => {
    (async () => {
      const token = localStorage.getItem("accessToken");
      if (token) {
        API.defaults.headers.common.Authorization = `Bearer ${token}`;
        try {
          const { data } = await API.get<UsuarioPerfil>("/users/me/");
          setUser(data);
        } catch {
          // Token inválido o expirado
          localStorage.removeItem("accessToken");
          localStorage.removeItem("refreshToken");
          localStorage.removeItem("accessTokenExp");
        }
      }
      setInit(false);
    })();
  }, []);

  const login = async (username: string, password: string) => {
    // 1) Pedimos tokens
    const { data } = await API.post<{ access: string; refresh: string }>(
      "/token/",
      { username, password }
    );

    // 2) Guardamos tokens y expiración del access
    localStorage.setItem("accessToken", data.access);
    localStorage.setItem("refreshToken", data.refresh);
    const expiresAt = dayjs().add(1, "hour").unix().toString(); 
    localStorage.setItem("accessTokenExp", expiresAt);

    // 3) Inyectamos el header por defecto
    API.defaults.headers.common.Authorization = `Bearer ${data.access}`;

    // 4) Cargamos perfil y redirigimos
    const res = await API.get<UsuarioPerfil>("/users/me/");
    setUser(res.data);
    navigate("/");
  };

  const logout = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("accessTokenExp");
    delete API.defaults.headers.common.Authorization;
    setUser(null);
    navigate("/login");
  };

  if (init) return null;

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
