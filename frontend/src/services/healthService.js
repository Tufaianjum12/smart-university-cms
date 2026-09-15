// Wraps the /api/v1/health backend endpoint.
//
// Pages never call apiClient directly — they call a function from a
// service file like this one. This keeps every backend endpoint's exact
// path and shape defined in exactly one place per module.

import apiClient from "./apiClient";

const API_V1_PREFIX = "/api/v1";

export async function fetchHealth() {
  const response = await apiClient.get(`${API_V1_PREFIX}/health`);
  return response.data;
}
