import { createBrowserRouter } from "react-router-dom";
import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { DashboardLayout } from "@/features/dashboard/components/DashboardLayout";
import { DashboardPage } from "@/features/dashboard/pages/DashboardPage";
import { EventFormPage } from "@/features/events/pages/EventFormPage";
import { EventsListPage } from "@/features/events/pages/EventsListPage";
import { FinanceTransactionFormPage } from "@/features/finance/pages/FinanceTransactionFormPage";
import { FinanceTransactionsListPage } from "@/features/finance/pages/FinanceTransactionsListPage";
import { LeadershipFormPage } from "@/features/leaderships/pages/LeadershipFormPage";
import { LeadershipsListPage } from "@/features/leaderships/pages/LeadershipsListPage";
import { MapPage } from "@/features/map/pages/MapPage";
import { PublicRegistrationPage } from "@/features/public-registration/pages/PublicRegistrationPage";
import { RegistrationLinkPage } from "@/features/registration-link/pages/RegistrationLinkPage";
import { VoterFormPage } from "@/features/voters/pages/VoterFormPage";
import { VotersListPage } from "@/features/voters/pages/VotersListPage";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    // Rota PÚBLICA, de propósito fora do ProtectedRoute — quem abre esse
    // link não tem (nem precisa ter) conta no sistema.
    path: "/cadastro/:token",
    element: <PublicRegistrationPage />,
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
          { path: "/liderancas", element: <LeadershipsListPage /> },
          { path: "/liderancas/novo", element: <LeadershipFormPage /> },
          { path: "/liderancas/:id/editar", element: <LeadershipFormPage /> },
          { path: "/agenda", element: <EventsListPage /> },
          { path: "/agenda/novo", element: <EventFormPage /> },
          { path: "/agenda/:id/editar", element: <EventFormPage /> },
          { path: "/financeiro", element: <FinanceTransactionsListPage /> },
          { path: "/financeiro/novo", element: <FinanceTransactionFormPage /> },
          { path: "/financeiro/:id/editar", element: <FinanceTransactionFormPage /> },
          { path: "/mapa", element: <MapPage /> },
          { path: "/link-cadastro", element: <RegistrationLinkPage /> },
        ],
      },
    ],
  },
]);
