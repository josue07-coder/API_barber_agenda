import { Navigate } from "react-router-dom";
import { AdminDashboardPage } from "@/features/dashboard/AdminDashboardPage";
import { BarberDashboardPage } from "@/features/dashboard/BarberDashboardPage";
import { useAuthStore } from "@/stores/auth.store";

export function DashboardPage() {
  const user = useAuthStore((state) => state.user);

  if (user?.role === "admin") return <AdminDashboardPage />;
  if (user?.role === "barber") return <BarberDashboardPage />;
  return <Navigate to="/app/client/dashboard" replace />;
}
