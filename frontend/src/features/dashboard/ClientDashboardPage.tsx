import { useQuery } from "@tanstack/react-query";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatMoney } from "@/lib/formatters";
import { getClientDashboardData } from "@/services/client.api";
import { MetricCard } from "@/features/dashboard/MetricCard";

export function ClientDashboardPage() {
  const query = useQuery({
    queryKey: ["client-dashboard"],
    queryFn: getClientDashboardData
  });

  if (query.isLoading) return <LoadingState label="Cargando tu cuenta..." />;
  if (query.isError) return <ErrorState message="No se pudo cargar tu panel" onRetry={() => query.refetch()} />;

  const data = query.data!;
  const paid = data.payments.reduce((total, payment) => {
    if (payment.status !== "paid" && payment.status !== "partially_paid") return total;
    return total + Number(payment.amount);
  }, 0);
  const nextAppointment = data.appointments
    .filter((appointment) => ["agendada", "confirmada"].includes(appointment.status))
    .sort((a, b) => `${a.date} ${a.start_time}`.localeCompare(`${b.date} ${b.start_time}`))[0];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Mi panel</h1>
        <p className="text-sm text-muted-foreground">Citas, pagos y notificaciones de tu cuenta.</p>
      </div>
      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Mis citas" value={data.appointments.length} />
        <MetricCard label="Pagado" value={formatMoney(paid)} />
        <MetricCard label="Notificaciones" value={data.notifications.length} />
      </section>
      <Card>
        <CardHeader>
          <CardTitle>Proxima cita</CardTitle>
        </CardHeader>
        <CardContent>
          {nextAppointment ? (
            <div className="rounded-md border p-3 text-sm">
              <p className="font-medium">Cita #{nextAppointment.id}</p>
              <p className="text-muted-foreground">
                {nextAppointment.date} {nextAppointment.start_time} · {nextAppointment.status}
              </p>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No tienes citas proximas.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
