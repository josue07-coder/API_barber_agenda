import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { defaultDateRange, formatMoney } from "@/lib/formatters";
import { getDashboardOverview } from "@/services/dashboard.api";
import { useAuthStore } from "@/stores/auth.store";
import type { DashboardFilters } from "@/types/api";
import { DashboardFilters as Filters } from "@/features/dashboard/DashboardFilters";
import { MetricCard } from "@/features/dashboard/MetricCard";

export function BarberDashboardPage() {
  const user = useAuthStore((state) => state.user);
  const [filters, setFilters] = useState<DashboardFilters>({
    ...defaultDateRange(),
    branch_id: user?.branch_id ?? undefined,
    barber_id: user?.id
  });

  const query = useQuery({
    queryKey: ["dashboard", "overview", "barber", filters],
    queryFn: () => getDashboardOverview(filters)
  });

  if (query.isLoading) return <LoadingState label="Cargando tus metricas..." />;
  if (query.isError) return <ErrorState message="No se pudo cargar tu dashboard" onRetry={() => query.refetch()} />;

  const data = query.data!;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard barber</h1>
        <p className="text-sm text-muted-foreground">Tu agenda, ingresos y pagos pendientes.</p>
      </div>
      <Filters
        value={filters}
        onChange={(next) =>
          setFilters({
            ...next,
            branch_id: user?.branch_id ?? undefined,
            barber_id: user?.id
          })
        }
      />
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Mis citas" value={data.totals.total_appointments} />
        <MetricCard label="Completadas" value={data.totals.completed_appointments} />
        <MetricCard label="Ingresos netos" value={formatMoney(data.totals.net_revenue)} />
        <MetricCard label="No-show" value={data.totals.no_show_appointments} />
      </section>
      <Card>
        <CardHeader>
          <CardTitle>Mis proximas citas de hoy</CardTitle>
        </CardHeader>
        <CardContent>
          {data.upcoming_appointments_today.length === 0 ? (
            <p className="text-sm text-muted-foreground">No tienes citas proximas para hoy.</p>
          ) : (
            <div className="grid gap-2 md:grid-cols-2">
              {data.upcoming_appointments_today.map((appointment) => (
                <div key={appointment.id} className="rounded-md border p-3 text-sm">
                  <p className="font-medium">Cita #{appointment.id}</p>
                  <p className="text-muted-foreground">
                    {appointment.start_time} · cliente #{appointment.client_id}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
