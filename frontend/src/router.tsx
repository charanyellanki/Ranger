import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { Dashboard } from "./pages/Dashboard";
import { AlertDetail } from "./pages/AlertDetail";
import { Runbooks } from "./pages/Runbooks";
import { AdminSettings } from "./pages/AdminSettings";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "alerts/:alertId", element: <AlertDetail /> },
      { path: "runbooks", element: <Runbooks /> },
      { path: "admin/settings", element: <AdminSettings /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);
