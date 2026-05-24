# BARBER_AGENDA Frontend Contract

Guia para construir un frontend SaaS sobre la API `BARBER_AGENDA`.

Base URL sugerida en desarrollo:

```text
http://127.0.0.1:8000/api/v1
```

## Stack Recomendado

- React + Vite
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- Zustand para auth/UI global o Context si se prefiere algo minimo
- Recharts para dashboards
- React Hook Form + Zod
- Axios o `fetch` wrapper propio
- date-fns para fechas

## Modulos Disponibles

- Auth y sesion
- Usuarios y barberos
- Clientes
- Perfil cliente/autoservicio
- Servicios
- Sucursales y configuracion por sucursal
- Agenda/citas
- Horarios por barbero
- Bloqueos de agenda
- Pagos y depositos
- Caja y movimientos
- Comisiones
- Penalizaciones y reputacion
- Inventario y ventas POS
- Notificaciones y recordatorios
- Dashboard frontend
- Reportes financieros, operativos y exportaciones

## Roles

### admin

Ve y gestiona todo:

- Dashboard global.
- Usuarios, barberos, clientes, servicios y sucursales.
- Horarios, bloqueos, citas, pagos, caja, comisiones, inventario, reportes y notificaciones.
- Puede filtrar por sucursal y barbero.

### barber

Opera su agenda y sucursal:

- Dashboard limitado a sus metricas y su sucursal.
- Sus citas, horarios, bloqueos, disponibilidad y pagos relacionados.
- Caja de su sucursal si aplica.
- Venta de productos y consulta de stock de su sucursal.
- Consulta de comisiones propias.
- Notificaciones relacionadas.

### client

Autoservicio:

- Login/registro.
- Ver perfil.
- Ver, crear, cancelar y reprogramar sus citas bajo reglas.
- Ver pagos, notificaciones, historial y penalizaciones propias.
- No accede a dashboard administrativo, caja, reportes, inventario administrativo ni comisiones.

## Manejo de Auth/JWT

Login usa `application/x-www-form-urlencoded`:

```text
POST /auth/login
username=<email>&password=<password>
```

Guardar `access_token` en memoria + storage persistente si el producto requiere sesion persistente. Para MVP se puede usar `localStorage`, pero una version mas robusta deberia migrar a cookies httpOnly cuando exista soporte backend.

Enviar:

```http
Authorization: Bearer <TOKEN>
```

Bootstrap recomendado:

1. Login o carga de token persistido.
2. `GET /me` para conocer `role`, `id`, `branch_id`, `client_id`.
3. Guardar usuario en `authStore`.
4. Aplicar guards por rol en rutas.

Estados globales:

- `auth.user`
- `auth.token`
- `auth.isAuthenticated`
- `auth.role`
- `ui.sidebarCollapsed`
- `filters.branchId`
- `filters.dateRange`

## Estructura Frontend Recomendada

```text
src/
  app/
    router.tsx
    providers.tsx
  components/
    layout/
      AppShell.tsx
      Sidebar.tsx
      Topbar.tsx
      RoleGuard.tsx
    common/
      DataTable.tsx
      EmptyState.tsx
      ErrorState.tsx
      LoadingState.tsx
      ConfirmDialog.tsx
      DateRangePicker.tsx
      BranchSelect.tsx
      BarberSelect.tsx
    dashboard/
      MetricCard.tsx
      RevenueChart.tsx
      StatusDonut.tsx
      TopList.tsx
    appointments/
      CalendarView.tsx
      AppointmentDrawer.tsx
      AppointmentForm.tsx
      AvailableSlotsPicker.tsx
    pos/
      ProductSearch.tsx
      ProductSaleForm.tsx
      CashSessionPanel.tsx
  features/
    auth/
    dashboard/
    appointments/
    clients/
    barbers/
    services/
    branches/
    payments/
    cash/
    commissions/
    notifications/
    reports/
    inventory/
    profile/
  hooks/
    useAuth.ts
    useRoleGuard.ts
    useDashboardFilters.ts
  lib/
    api.ts
    queryClient.ts
    routes.ts
    formatters.ts
  services/
    auth.api.ts
    dashboard.api.ts
    appointments.api.ts
    clients.api.ts
    users.api.ts
    services.api.ts
    branches.api.ts
    payments.api.ts
    cash.api.ts
    commissions.api.ts
    notifications.api.ts
    reports.api.ts
    inventory.api.ts
  stores/
    auth.store.ts
    ui.store.ts
  schemas/
    appointment.schema.ts
    client.schema.ts
    service.schema.ts
    branch.schema.ts
```

## Rutas Frontend Sugeridas

### Publicas

- `/login`
- `/register-client`

### App admin

- `/app/dashboard`
- `/app/calendar`
- `/app/clients`
- `/app/barbers`
- `/app/services`
- `/app/branches`
- `/app/payments`
- `/app/cash`
- `/app/commissions`
- `/app/inventory`
- `/app/notifications`
- `/app/reports`
- `/app/settings`

### App barber

- `/app/dashboard`
- `/app/calendar`
- `/app/my-schedule`
- `/app/clients`
- `/app/payments`
- `/app/cash`
- `/app/my-commissions`
- `/app/pos`
- `/app/notifications`

### App client

- `/app/client/dashboard`
- `/app/client/appointments`
- `/app/client/book`
- `/app/client/payments`
- `/app/client/notifications`
- `/app/client/penalties`
- `/app/client/profile`

## Guards por Rol

```ts
type Role = "admin" | "barber" | "client";

const routeRoles: Record<string, Role[]> = {
  "/app/dashboard": ["admin", "barber"],
  "/app/reports": ["admin"],
  "/app/cash": ["admin", "barber"],
  "/app/commissions": ["admin"],
  "/app/my-commissions": ["barber"],
  "/app/client/profile": ["client"],
};
```

Reglas:

- Sin token: redirigir a `/login`.
- Token invalido o `401`: limpiar sesion y redirigir.
- `403`: mostrar pantalla de acceso denegado.
- Client nunca debe ver navegacion admin/barber.

## Contrato por Pantalla

### Login

Endpoints:

- `POST /auth/login`
- `POST /auth/register-client`
- `POST /auth/register` solo bootstrap primer admin.
- `GET /me`

Componentes:

- `LoginForm`
- `RegisterClientForm`
- `AuthLayout`

Estados:

- loading al enviar.
- error `400` credenciales.
- error `429` rate limit.
- redirect por rol al terminar login.

### Dashboard Admin

Endpoints:

- `GET /dashboard/overview`
- `GET /dashboard/financial`
- `GET /dashboard/appointments`
- `GET /dashboard/barbers`
- `GET /dashboard/clients`
- `GET /dashboard/branches`
- `GET /branches/`
- `GET /users/`

Filtros:

- `start_date`
- `end_date`
- `branch_id`
- `barber_id`

Componentes:

- `DashboardFilters`
- `MetricCardGrid`
- `RevenueLineChart`
- `PaymentMethodBarChart`
- `AppointmentStatusChart`
- `BranchComparisonTable`
- `TopServicesList`
- `TopBarbersList`

Response esperado:

- `overview.totals.total_appointments`
- `overview.totals.total_revenue`
- `financial.revenue_by_day[]`
- `appointments.appointments_by_status[]`
- `barbers.revenue_per_barber[]`
- `clients.top_clients_by_revenue[]`
- `branches.branch_comparison[]`

Estados:

- skeleton cards.
- empty charts si arrays vacios.
- error `403` si rol no permitido.

### Dashboard Barber

Endpoints:

- `GET /dashboard/overview`
- `GET /dashboard/financial`
- `GET /dashboard/appointments`
- `GET /dashboard/barbers`
- `GET /me`
- `GET /notifications/`

Notas:

- No enviar `barber_id` distinto al usuario actual.
- Si se envia `branch_id`, debe coincidir con `user.branch_id`.

Componentes:

- `BarberTodayPanel`
- `MyRevenueCards`
- `MyAppointmentsChart`
- `MyCommissionsSummary`
- `TodayAppointmentsList`

### Dashboard Client

No usar `/dashboard/*`, porque client recibe `403`.

Endpoints:

- `GET /me`
- `GET /me/appointments`
- `GET /me/payments`
- `GET /me/notifications`
- `GET /me/penalties`

Componentes:

- `ClientNextAppointmentCard`
- `ClientAppointmentsList`
- `ClientPaymentHistory`
- `ClientPenaltyStatus`
- `BookAppointmentCTA`

### Agenda / Calendario

Endpoints:

- `GET /appointments/`
- `GET /appointments/day?barber_id=&date=`
- `GET /appointments/barber/{barber_id}`
- `GET /appointments/client/{client_id}`
- `GET /appointments/available-slots?barber_id=&service_id=&date=&branch_id=`
- `POST /appointments/`
- `PATCH /appointments/{id}/confirm`
- `PATCH /appointments/{id}/complete`
- `PATCH /appointments/{id}/no-show`
- `PATCH /appointments/{id}/cancel`
- `PATCH /appointments/{id}/reschedule`
- `GET /appointments/{id}/history`
- `GET /barber-schedules/barber/{barber_id}`
- `GET /barber-time-blocks/`

Componentes:

- `CalendarView`
- `AppointmentDrawer`
- `AppointmentForm`
- `AvailableSlotsPicker`
- `StatusActionButtons`
- `AppointmentHistoryTimeline`

Permisos:

- Admin: todas.
- Barber: sus citas.
- Client: sus citas mediante `/me/appointments` y crear/cancelar/reprogramar propias.

Estados:

- slot no disponible: `409`.
- fuera de horario/bloqueo: `400` o `409`.
- sin permiso: `403`.

### Clientes

Endpoints:

- `GET /clients/?search=`
- `GET /clients/{client_id}`
- `POST /clients/`
- `PUT /clients/{client_id}`
- `PUT /clients/delete/{client_id}`
- `GET /clients/{client_id}/penalties`
- `POST /clients/{client_id}/penalties`

Componentes:

- `ClientsTable`
- `ClientForm`
- `ClientDetailDrawer`
- `ClientPenaltiesPanel`
- `ClientAppointmentHistory`

Permisos:

- Admin gestiona.
- Barber puede necesitar vista limitada via citas/agenda.
- Client usa perfil propio, no esta pantalla.

### Barberos

Endpoints:

- `POST /auth/barbers`
- `GET /users/`
- `GET /users/{user_id}`
- `PUT /users/{user_id}`
- `DELETE /users/{user_id}/deactivate`
- `GET /barber-schedules/barber/{barber_id}`
- `POST /barber-schedules/`
- `PUT /barber-schedules/{schedule_id}`
- `PATCH /barber-schedules/{schedule_id}/activate`
- `PATCH /barber-schedules/{schedule_id}/deactivate`
- `GET /barber-time-blocks/?barber_id=`
- `POST /barber-time-blocks/`

Componentes:

- `BarbersTable`
- `BarberForm`
- `ScheduleEditor`
- `TimeBlocksManager`
- `BarberPerformanceTab`

### Servicios

Endpoints:

- `GET /services/?search=&branch_id=`
- `GET /services/{service_id}`
- `POST /services/`
- `PUT /services/{service_id}`
- `DELETE /services/{service_id}`

Componentes:

- `ServicesTable`
- `ServiceForm`
- `ServiceStatusBadge`

### Sucursales

Endpoints:

- `GET /branches/`
- `GET /branches/{branch_id}`
- `POST /branches/`
- `PUT /branches/{branch_id}`
- `DELETE /branches/{branch_id}`
- `GET /branches/{branch_id}/settings`
- `PUT /branches/{branch_id}/settings`

Componentes:

- `BranchesTable`
- `BranchForm`
- `BranchSettingsForm`
- `BusinessRulesPanel`

### Pagos

Endpoints:

- `POST /payments/`
- `GET /payments/{payment_id}`
- `GET /payments/appointment/{appointment_id}`
- `PATCH /payments/{payment_id}/mark-paid`
- `PATCH /payments/{payment_id}/refund`
- `GET /payments/summary`
- Client: `GET /me/payments`

Componentes:

- `PaymentForm`
- `AppointmentPaymentsTable`
- `RefundDialog`
- `PaymentSummaryCards`

Estados:

- pago en cita cancelada: `400`.
- pago cash sin caja abierta: `409`.
- sin permiso: `403`.

### Caja

Endpoints:

- `POST /cash-sessions/open`
- `PATCH /cash-sessions/{session_id}/close`
- `GET /cash-sessions/current?branch_id=`
- `GET /cash-sessions/{session_id}`
- `POST /cash-movements/`
- `GET /cash-movements/session/{session_id}`

Componentes:

- `CashSessionStatus`
- `OpenCashDialog`
- `CloseCashDialog`
- `CashMovementsTable`
- `ManualCashMovementForm`

Permisos:

- Admin todas las sucursales.
- Barber solo su sucursal.

### Comisiones

Endpoints:

- `POST /commissions/rules`
- `GET /commissions/rules`
- `PUT /commissions/rules/{rule_id}`
- `PATCH /commissions/rules/{rule_id}/deactivate`
- `GET /commissions/`
- `GET /commissions/barber/{barber_id}`
- `PATCH /commissions/{commission_id}/approve`
- `PATCH /commissions/{commission_id}/mark-paid`
- `GET /commissions/summary`

Componentes:

- `CommissionRulesTable`
- `CommissionRuleForm`
- `CommissionsTable`
- `CommissionSummaryCards`

Permisos:

- Admin gestiona reglas/aprueba/paga.
- Barber ve propias.

### Inventario y POS

Endpoints:

- `POST /products/`
- `GET /products/`
- `GET /products/{product_id}`
- `PUT /products/{product_id}`
- `PATCH /products/{product_id}/deactivate`
- `GET /products/low-stock`
- `POST /inventory/movements`
- `GET /inventory/movements`
- `POST /product-sales/`
- `GET /product-sales/`
- `GET /reports/products`

Componentes:

- `ProductsTable`
- `ProductForm`
- `LowStockAlert`
- `InventoryMovementsTable`
- `ProductSaleForm`
- `POSCart`

Permisos:

- Admin gestiona todo.
- Barber vende y consulta stock de su sucursal.
- Client sin acceso.

### Notificaciones

Endpoints:

- `GET /notifications/`
- `GET /notifications/{notification_id}`
- `PATCH /notifications/{notification_id}/mark-sent`
- `PATCH /notifications/{notification_id}/mark-failed`
- `PATCH /notifications/{notification_id}/cancel`
- `POST /notifications/generate-reminders`
- Client: `GET /me/notifications`

Componentes:

- `NotificationList`
- `NotificationBadge`
- `NotificationActions`

### Reportes

Endpoints:

- `GET /reports/dashboard`
- `GET /reports/financial/by-barber`
- `GET /reports/financial/by-service`
- `GET /reports/financial/by-branch`
- `GET /reports/financial/by-method`
- `GET /reports/financial/daily`
- `GET /reports/financial/monthly`
- `GET /reports/financial/pending-balances`
- `GET /reports/financial/by-barber/export/csv`
- `GET /reports/financial/by-barber/export/excel`
- `GET /reports/clients/frequent`
- `GET /reports/clients/no-show`
- `GET /reports/clients/penalties`
- `GET /reports/products`
- `GET /reports/operations/hours`
- `GET /reports/operations/days`

Componentes:

- `ReportsFilterBar`
- `ExportButtons`
- `FinancialReportTables`
- `OperationalCharts`

### Perfil Cliente

Endpoints:

- `GET /me`
- `GET /me/appointments`
- `GET /me/payments`
- `GET /me/notifications`
- `GET /me/penalties`
- `PATCH /me/client-profile`
- `POST /appointments/`
- `PATCH /appointments/{id}/cancel`
- `PATCH /appointments/{id}/reschedule`
- `GET /appointments/{id}/history`

Componentes:

- `ClientProfileForm`
- `MyAppointments`
- `BookAppointmentWizard`
- `MyPayments`
- `MyNotifications`
- `MyPenalties`

## Servicios API Frontend

Ejemplo de wrapper:

```ts
export async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const token = authStore.getState().token;
  const res = await fetch(`${import.meta.env.VITE_API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => null);
    throw new ApiError(res.status, error?.message ?? "Error inesperado", error);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}
```

TanStack Query keys:

```ts
["me"]
["dashboard", "overview", filters]
["appointments", filters]
["clients", search]
["branches"]
["services", filters]
["payments", appointmentId]
["cash-session", branchId]
["notifications", page]
```

## Estados de Carga y Error

Usar un patron consistente:

- Loading inicial: skeleton.
- Refetch: conservar datos anteriores y mostrar spinner pequeño.
- Empty: `EmptyState` con accion primaria.
- Error 401: logout.
- Error 403: `ForbiddenState`.
- Error 409: toast accionable, por ejemplo horario ocupado o stock insuficiente.
- Error 422: mapear detalles a campos del formulario.
- Error 500: mensaje generico con `request_id` si llega en respuesta.

Formato de error backend:

```json
{
  "success": false,
  "message": "No tienes permiso",
  "error_code": "forbidden",
  "details": {},
  "request_id": "..."
}
```

## Riesgos y Endpoints Faltantes para Frontend

- `clients` no expone `created_at`; el dashboard infiere clientes nuevos desde citas.
- No existe endpoint dedicado para disponibilidad por rango semanal/mensual; el calendario puede necesitar llamar disponibilidad por dia.
- No hay endpoint para marcar notificacion como leida, solo estados de envio.
- No existe refresh token; el frontend debe manejar expiracion de JWT con logout.
- No hay paginacion avanzada uniforme en todos los listados.
- No hay endpoint de busqueda global.
- No hay endpoint especifico para detalle completo de cita con joins de cliente/barbero/servicio; el frontend puede requerir llamadas adicionales.
- Las exportaciones CSV/Excel existen para reportes financieros, pero no para todos los modulos.
