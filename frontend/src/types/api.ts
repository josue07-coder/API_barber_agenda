export type Role = "admin" | "barber" | "client";

export type User = {
  id: number;
  name: string;
  email: string;
  role: Role;
  client_id?: number | null;
  branch_id?: number | null;
  is_active: boolean;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type ApiErrorBody = {
  success?: false;
  message?: string;
  error_code?: string;
  details?: Record<string, unknown>;
  request_id?: string;
};

export type DashboardFilters = {
  start_date: string;
  end_date: string;
  branch_id?: number;
  barber_id?: number;
};

export type MetricTotals = {
  total_appointments: number;
  completed_appointments: number;
  cancelled_appointments: number;
  no_show_appointments: number;
  total_revenue: number;
  total_refunds: number;
  net_revenue: number;
  pending_payments: number;
  active_clients: number;
  new_clients: number;
};

export type DashboardItem = {
  id?: number;
  label: string;
  value: number;
};

export type AppointmentPreview = {
  id: number;
  date: string;
  start_time: string;
  status: string;
  client_id: number;
  barber_id: number;
  service_id: number;
  branch_id?: number | null;
};

export type DashboardOverview = {
  totals: MetricTotals;
  top_services: DashboardItem[];
  top_barbers: DashboardItem[];
  upcoming_appointments_today: AppointmentPreview[];
};

export type Appointment = {
  id: number;
  date: string;
  start_time: string;
  end_time: string;
  status: string;
  payment_status: string;
  user_id: number;
  client_id: number;
  service_id: number;
  branch_id?: number | null;
};

export type Payment = {
  id: number;
  appointment_id: number;
  client_id: number;
  amount: string | number;
  currency: string;
  payment_method: string;
  status: string;
  paid_at?: string | null;
  refunded_at?: string | null;
};

export type Notification = {
  id: number;
  recipient_type: string;
  recipient_id: number;
  subject: string;
  message: string;
  status: string;
  related_type?: string | null;
  related_id?: number | null;
};
