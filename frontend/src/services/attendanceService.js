import apiClient from "./apiClient";

const base = "/api/v1/attendance";

export const attendanceApi = {
  sessions: (params = {}) => apiClient.get(`${base}/sessions`, { params }),
  createSession: (data) => apiClient.post(`${base}/sessions`, data),
  getSession: (id) => apiClient.get(`${base}/sessions/${id}`),
  updateSession: (id, data) => apiClient.patch(`${base}/sessions/${id}`, data),
  sessionEnrollments: (id) => apiClient.get(`${base}/sessions/${id}/enrollments`),
  records: (id) => apiClient.get(`${base}/sessions/${id}/records`),
  markBulk: (id, data) => apiClient.post(`${base}/sessions/${id}/records`, data),
  updateRecord: (id, data) => apiClient.patch(`${base}/records/${id}`, data),
  offeringSummary: (id) => apiClient.get(`${base}/course-offerings/${id}/summary`),
  mySummary: (id) => apiClient.get(`${base}/student/me/${id}`),\n  myHistory: (params = {}) => apiClient.get(`${base}/student/me`, { params }),
};
