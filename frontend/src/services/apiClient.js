import axios from "axios";
import { TOKEN_KEY } from "../context/AuthContext";
const apiClient = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000", timeout: 10000 });
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
export default apiClient;

apiClient.interceptors.response.use(r => r, error => {
  if (error.response?.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    window.dispatchEvent(new Event("auth-expired"));
  }
  return Promise.reject(error);
});
