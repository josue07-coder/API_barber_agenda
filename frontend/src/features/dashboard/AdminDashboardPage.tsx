import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDashboardOverview } from "@/services/dashboard.api";
import { formatMoney, defaultDateRange } from "@/lib/formatters";
import type { DashboardFilters } from "@/types/api";
import { DashboardFilters as Filters } from "@/features/dashboard/DashboardFilters";
import { MetricCard } from "@/features/dashboard/MetricCard";

export function AdminDashboardPage() {
  const [filters, setFilters] = useState<DashboardFilters>(defaultDateRange());
  const query = useQuery({
    queryKey: ["dashboard", "overview", filters],
    queryFn: () => getDashboardOverview(filters)
  });

  if (query.isLoading) return <LoadingState label="Cargando dashboard..." />;
  if (query.isError) return <ErrorState message="No se pudo cargar el dashboard" onRetry={() => query.refetch()} />;

  const data = query.data!;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard admin</h1>
        <p className="text-sm text-muted-foreground">Resumen operativo y financiero global.</p>
      </div>
      <Filters value={filters} onChange={setFilters} />
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Citas" value={data.totals.total_appointments} />
        <MetricCard label="Completadas" value={data.totals.completed_appointments} />
        <MetricCard label="Ingresos netos" value={formatMoney(data.totals.net_revenue)} />
        <MetricCard label="Pagos pendientes" value={data.totals.pending_payments} />
      </section>
      <section className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Servicios principales</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.top_services}>
                <XAxis dataKey="label" tickLine={false} axisLine={false} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                <Tooltip />
                <Bar dataKey="value" fill="hsl(var(--primary))" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Proximas citas de hoy</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.upcoming_appointments_today.length === 0 ? (
                <p className="text-sm text-muted-foreground">No hay citas proximas.</p>
              ) : (
                data.upcoming_appointments_today.map((appointment) => (
                  <div key={appointment.id} className="rounded-md border p-3 text-sm">
                    <p className="font-medium">Cita #{appointment.id}</p>
                    <p className="text-muted-foreground">
                      {appointment.date} {appointment.start_time} · {appointment.status}
                    </p>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
