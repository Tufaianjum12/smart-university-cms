// App root — mounts the route tree. Kept intentionally thin; all real
// structure lives in routes/AppRoutes.jsx and layouts/MainLayout.jsx.

import AppRoutes from "./routes/AppRoutes";

export default function App() {
  return <AppRoutes />;
}
