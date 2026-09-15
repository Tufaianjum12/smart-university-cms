// Route definitions.
//
// Phase 1 only needs one real route: the foundation status page. Future
// phases add routes here (and, once auth exists, wrap protected ones in
// a ProtectedRoute component) without touching App.jsx.

import { Routes, Route } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import StatusPage from "../pages/StatusPage";

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<StatusPage />} />
      </Route>
    </Routes>
  );
}
