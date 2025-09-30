// src/api/axios.ts
import axios from "axios";
import dayjs from "dayjs";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/",
  headers: { "Content-Type": "application/json" },
  withCredentials: false, // Cambia a true si usas cookies
});

// Antes de cada petición comprobamos el token...
API.interceptors.request.use(async (config) => {
  const access = localStorage.getItem("accessToken");
  const refresh = localStorage.getItem("refreshToken");
  const expUnix = localStorage.getItem("accessTokenExp"); // timestamp Unix en string

  if (access && expUnix) {
    const exp = dayjs.unix(parseInt(expUnix));
    // Si queda menos de 1 minuto de vida, hacemos refresh
    if (dayjs().add(1, "minute").isAfter(exp) && refresh) {
      try {
        const { data } = await axios.post(
          `${API.defaults.baseURL}token/refresh/`,
          { refresh }
        );
        // Guardamos nuevo access y su expiración
        localStorage.setItem("accessToken", data.access);
        const newExp = dayjs().add(1, "hour").unix().toString();
        localStorage.setItem("accessTokenExp", newExp);

        // Inyectamos el header con el nuevo token
        config.headers = config.headers ?? {};
        config.headers.Authorization = `Bearer ${data.access}`;
        return config;
      } catch {
        // Si refresh falla, limpiamos y dejamos que capture el login
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        localStorage.removeItem("accessTokenExp");
      }
    }

    // Token aún válido: lo inyectamos
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${access}`;
  }

  return config;
});
export default API;
