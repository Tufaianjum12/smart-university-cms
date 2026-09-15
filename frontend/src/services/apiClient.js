// Centralized Axios instance.
//
// Every API call in the app goes through this client instead of calling
// axios.get(...)/axios.post(...) directly with hard-coded URLs scattered
// across components. Benefits:
//   - The backend base URL lives in exactly one place, driven by an
//     environment variable (VITE_API_BASE_URL), so switching between
//     local/staging/production backends never touches component code.
//   - When JWT auth arrives (Phase 3), the Authorization header is added
//     once here via an interceptor, and every existing call automatically
//     gets it.
//   - Response/error handling conventions can evolve in one place.

import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Placeholder for Phase 3: once JWT auth exists, an interceptor here will
// attach `Authorization: Bearer <token>` to every outgoing request.
// apiClient.interceptors.request.use((config) => { ... return config; });

export default apiClient;
