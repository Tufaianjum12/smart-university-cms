import apiClient from "./apiClient";

const base = "/api/v1/attendance/analytics";

export const attendanceAnalyticsApi = {
  policy: () => apiClient.get(`${base}/policy`),
  mySummary: (offeringId, futureClassesAvailable) =>
    apiClient.get(`${base}/student/me/${offeringId}`, {
      params:
        futureClassesAvailable === "" || futureClassesAvailable == null
          ? {}
          : { future_classes_available: futureClassesAvailable },
    }),
  myTrend: (offeringId) => apiClient.get(`${base}/student/me/${offeringId}/trend`),
  course: (offeringId) => apiClient.get(`${base}/course-offerings/${offeringId}`),
  recovery: (params) => apiClient.get(`${base}/recovery`, { params }),
  maximumAbsences: (params) => apiClient.get(`${base}/maximum-absences`, { params }),
};
