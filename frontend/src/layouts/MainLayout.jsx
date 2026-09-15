// Shared shell around every page: a top nav bar and a content outlet.
// Role-specific layouts (StudentLayout, AdminLayout, ...) will be added
// alongside this one in later phases once roles/dashboards exist.

import { Outlet } from "react-router-dom";

export default function MainLayout() {
  return (
    <div className="d-flex flex-column min-vh-100">
      <header className="border-bottom">
        <div className="container py-3 d-flex align-items-center gap-2">
          <i className="bi bi-mortarboard-fill fs-4" style={{ color: "#2c4a52" }} />
          <span className="fw-semibold fs-5" style={{ color: "#1b2e33" }}>
            Smart University CMS
          </span>
        </div>
      </header>

      <main className="flex-grow-1">
        <Outlet />
      </main>

      <footer className="border-top py-3">
        <div className="container text-center text-muted small">
          Smart University Academic Management System — Phase 1 foundation
        </div>
      </footer>
    </div>
  );
}
