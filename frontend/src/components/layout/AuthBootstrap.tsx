import { useEffect } from "react";
import { useAuthStore } from "@/stores/auth.store";

export function AuthBootstrap() {
  const bootstrap = useAuthStore((state) => state.bootstrap);
  const token = useAuthStore((state) => state.token);

  useEffect(() => {
    if (token) void bootstrap();
  }, [bootstrap, token]);

  return null;
}
