// Phase 1's one real page.
//
// Its purpose is narrow and honest: call the real FastAPI /health
// endpoint via Axios and display exactly what comes back — including a
// live PostgreSQL connectivity check — so there's visible proof the
// frontend, backend, and database can actually talk to each other.
// Student/teacher/admin dashboards are built in later phases.

import { useHealthCheck } from "../hooks/useHealthCheck";
import StatusDot from "../components/StatusDot";

export default function StatusPage() {
  const { data, error, status } = useHealthCheck();

  return (
    <div className="container py-5" style={{ maxWidth: 720 }}>
      <h1 className="mb-2" style={{ color: "#1b2e33", fontWeight: 600 }}>
        Development foundation is running
      </h1>
      <p className="text-muted mb-4">
        This page calls the real backend at <code>/api/v1/health</code> — nothing on this
        screen is hard-coded.
      </p>

      <div className="border rounded-3 p-4">
        {status === "loading" && (
          <p className="mb-0 text-muted">Contacting backend&hellip;</p>
        )}

        {status === "error" && (
          <>
            <StatusDot ok={false} label="Could not reach the backend" />
            <p className="text-muted small mt-3 mb-0">
              Make sure the FastAPI server is running on the URL configured in{" "}
              <code>VITE_API_BASE_URL</code> (default <code>http://localhost:8000</code>), and
              that its CORS settings allow this origin.
            </p>
          </>
        )}

        {status === "success" && data && (
          <div className="d-flex flex-column gap-3">
            <StatusDot ok={data.status === "ok"} label={`API: ${data.service}`} />
            <StatusDot
              ok={data.database?.connected}
              label={
                data.database?.connected
                  ? "Database: connected"
                  : `Database: not connected (${data.database?.detail})`
              }
            />
            <div className="text-muted small">Environment: {data.environment}</div>
          </div>
        )}
      </div>

      <p className="text-muted small mt-4 mb-0">
        Phase 1 — project setup only. Academic features begin in later phases.
      </p>
    </div>
  );
}
