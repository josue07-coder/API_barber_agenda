import { Navigate, Outlet, useLocation } from "react-router-dom";
import { LoadingState } from "@/components/common/LoadingState";
import { useAuthStore } from "@/stores/auth.store";
import type { Role } from "@/types/api";

export function RoleGuard({ roles }: { roles: Role[] }) {
  const location = useLocation();
  const token = useAuthStore((state) => state.token);
  const user = useAuthStore((state) => state.user);
  const isBootstrapping = useAuthStore((state) => state.isBootstrapping);

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (isBootstrapping || !user) {
    return <LoadingState label="Validando sesion..." />;
  }

  if (!roles.includes(user.role)) {
    return <Navigate to="/forbidden" replace />;
  }

  return <Outlet />;
}
