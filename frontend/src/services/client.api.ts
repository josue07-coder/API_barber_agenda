import { api } from "@/lib/api";
import type { Appointment, Notification, Payment, User } from "@/types/api";

export async function getClientDashboardData() {
  const [me, appointments, payments, notifications] = await Promise.all([
    api.get<User>("/me"),
    api.get<Appointment[]>("/me/appointments"),
    api.get<Payment[]>("/me/payments"),
    api.get<Notification[]>("/me/notifications")
  ]);

  return {
    me: me.data,
    appointments: appointments.data,
    payments: payments.data,
    notifications: notifications.data
  };
}
