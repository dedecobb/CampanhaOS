import { createBrowserRouter } from "react-router-dom";
import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { DashboardLayout } from "@/features/dashboard/components/DashboardLayout";
import { DashboardPage } from "@/features/dashboard/pages/DashboardPage";
import { VoterFormPage } from "@/features/voters/pages/VoterFormPage";
import { VotersListPage } from "@/features/voters/pages/VotersListPage";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <DashboardLayout />,
        children: [
          { path: "/", element: <DashboardPage /> },
          { path: "/eleitores", element: <VotersListPage /> },
          { path: "/eleitores/novo", element: <VoterFormPage /> },
          { path: "/eleitores/:id/editar", element: <VoterFormPage /> },
        ],
      },
    ],
  },
]);
