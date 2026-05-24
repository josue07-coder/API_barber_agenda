# BARBER_AGENDA API Examples

Base URL local:

```text
http://127.0.0.1:8000/api/v1
```

En los ejemplos, reemplaza:

- `<TOKEN>` por el JWT retornado en login.
- `<ADMIN_TOKEN>` por token de admin.
- `<BARBER_ID>`, `<CLIENT_ID>`, `<SERVICE_ID>`, `<APPOINTMENT_ID>` y `<PAYMENT_ID>` por IDs reales.

## 1. Crear Primer Admin

Solo funciona si no existe ningun admin.

```http
POST /auth/register
Content-Type: application/json
```

```json
{
  "name": "Admin Principal",
  "email": "admin@barber.local",
  "password": "Admin12345"
}
```

Response:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

Errores esperados:

- `403 forbidden`: ya existe un administrador.
- `422 validation_error`: datos invalidos.

## 2. Login

FastAPI usa OAuth2 form data, no JSON.

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded
```

```text
username=admin@barber.local&password=Admin12345
```

Response:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

Errores esperados:

- `400 bad_request`: credenciales invalidas.
- `429 rate_limited`: demasiados intentos.

## 3. Crear Barbero

Requiere admin.

```http
POST /auth/barbers
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

```json
{
  "name": "Carlos Barber",
  "email": "carlos@barber.local",
  "password": "Barber12345"
}
```

Response:

```json
{
  "id": 2,
  "name": "Carlos Barber",
  "email": "carlos@barber.local",
  "role": "barber",
  "is_active": true
}
```

## 4. Registrar Cliente Autenticado

```http
POST /auth/register-client
Content-Type: application/json
```

```json
{
  "name": "Juan Perez",
  "email": "juan@barber.local",
  "password": "Client12345",
  "phone": "8095551234",
  "notes": "Prefiere corte bajo"
}
```

Response:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

Este flujo crea un `User` con `role=client` y lo vincula a un registro `Client`.

Errores esperados:

- `400 bad_request`: email ya registrado o telefono ya asociado a otro usuario cliente.
- `422 validation_error`: datos invalidos.

## 5. Autoservicio Cliente

Perfil:

```http
GET /me
Authorization: Bearer <TOKEN_CLIENT>
```

Mis citas:

```http
GET /me/appointments
Authorization: Bearer <TOKEN_CLIENT>
```

Mis pagos:

```http
GET /me/payments
Authorization: Bearer <TOKEN_CLIENT>
```

Mis notificaciones:

```http
GET /me/notifications
Authorization: Bearer <TOKEN_CLIENT>
```

Editar mi perfil de cliente:

```http
PATCH /me/client-profile
Authorization: Bearer <TOKEN_CLIENT>
Content-Type: application/json
```

```json
{
  "name": "Juan Perez",
  "phone": "8095559876",
  "notes": "Prefiere la tarde"
}
```

Reglas:

- El cliente solo puede crear citas usando su propio `client_id`.
- El cliente solo ve citas, pagos y notificaciones propias.
- El cliente puede cancelar o reprogramar sus propias citas.
- El cliente no puede cancelar/reprogramar si falta menos de las horas configuradas en `CLIENT_CANCEL_CUTOFF_HOURS` o `CLIENT_RESCHEDULE_CUTOFF_HOURS`.
- El cliente no puede acceder a reportes, horarios ni bloqueos.
- `phone` es unico en `clients`; si hay duplicados existentes, la migracion falla hasta que se limpien.

## 6. Crear Cliente Administrativo

```http
POST /clients/
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

```json
{
  "name": "Juan Perez",
  "phone": "8095551234",
  "notes": "Prefiere corte bajo"
}
```

## 7. Crear Sucursal

Requiere admin.

```http
POST /branches/
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

```json
{
  "name": "Sucursal Centro",
  "address": "Av. Principal #10",
  "phone": "8095550000"
}
```

Asignar barbero a sucursal:

```http
PUT /users/<BARBER_USER_ID>
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

```json
{
  "branch_id": 1
}
```

Configurar reglas de sucursal:

```http
PUT /branches/1/settings
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

```json
{
  "timezone": "America/Santo_Domingo",
  "currency": "DOP",
  "default_cancel_cutoff_hours": 12,
  "default_reschedule_cutoff_hours": 12,
  "deposit_required": true,
  "default_deposit_amount": "250.00",
  "default_deposit_percentage": null,
  "reminder_24h_enabled": true,
  "reminder_2h_enabled": false
}
```

Reglas:

- Admin puede leer y actualizar settings de cualquier sucursal.
- Barber puede leer settings de su propia sucursal.
- Client recibe los efectos indirectos en cancelacion, reprogramacion, pagos y recordatorios.
- Si no hay settings para la sucursal, se usa la configuracion global.

## 8. Crear Servicio

Requiere admin.

```http
POST /services/
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

```json
{
  "name": "Corte clasico",
  "duration_minutes": 30,
  "price": "500.00",
  "branch_id": 1
}
```

## 9. Crear Horario de Barbero

`weekday`: 0=lunes, 1=martes, ..., 6=domingo.

Admin puede crear horarios de cualquier barbero. Barbero solo puede crear los propios.

```http
POST /barber-schedules/
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

```json
{
  "barber_id": 2,
  "weekday": 0,
  "start_time": "09:00:00",
  "end_time": "18:00:00",
  "break_start_time": "12:00:00",
  "break_end_time": "13:00:00",
  "is_active": true
}
```

Errores esperados:

- `409 conflict`: horario solapado.
- `403 forbidden`: barbero intentando gestionar otro barbero.

## 10. Crear Bloqueo Parcial

```http
POST /barber-time-blocks/
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

```json
{
  "barber_id": 2,
  "date": "2026-06-03",
  "start_time": "15:00:00",
  "end_time": "16:00:00",
  "reason": "Cita personal",
  "is_full_day": false,
  "is_active": true
}
```

## 11. Crear Bloqueo Dia Completo

```json
{
  "barber_id": 2,
  "date": "2026-06-04",
  "reason": "Vacaciones",
  "is_full_day": true,
  "is_active": true
}
```

## 12. Consultar Disponibilidad

```http
GET /appointments/available-slots?barber_id=2&service_id=1&date=2026-06-01&branch_id=1
Authorization: Bearer <TOKEN>
```

Response:

```json
{
  "slots": [
    "09:00:00",
    "09:30:00",
    "10:00:00"
  ]
}
```

La disponibilidad respeta:

- horario activo del barbero
- descansos
- bloqueos
- citas existentes
- buffer entre citas
- sucursal del barbero y servicio, si `branch_id` fue enviado

## 13. Crear Cita

```http
POST /appointments/
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

```json
{
  "barber_id": 2,
  "client_id": 1,
  "service_id": 1,
  "date": "2026-06-01",
  "start_time": "10:00:00",
  "branch_id": 1
}
```

Errores esperados:

- `400 bad_request`: fuera de horario, pasado o descanso.
- `403 forbidden`: barbero intentando crear cita para otro barbero.
- `409 conflict`: horario ocupado, bloqueado o doble reserva.
- `400 bad_request`: barbero o servicio no pertenece a la sucursal indicada.

## 14. Confirmar Cita

```http
PATCH /appointments/<APPOINTMENT_ID>/confirm
Authorization: Bearer <TOKEN>
```

Response:

```json
{
  "id": 1,
  "date": "2026-06-01",
  "start_time": "10:00:00",
  "end_time": "10:30:00",
  "status": "confirmada",
  "user_id": 2,
  "client_id": 1,
  "service_id": 1,
  "cancelled_at": null,
  "cancelled_by_user_id": null,
  "cancellation_reason": null
}
```

## 15. Reprogramar Cita

```http
PATCH /appointments/<APPOINTMENT_ID>/reschedule
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

```json
{
  "date": "2026-06-02",
  "start_time": "14:00:00"
}
```

## 16. Cancelar Cita

```http
PATCH /appointments/<APPOINTMENT_ID>/cancel
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

```json
{
  "reason": "Cliente solicito cancelar"
}
```

## 17. Registrar Pago o Deposito

```http
POST /payments/
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

```json
{
  "appointment_id": 1,
  "amount": "250.00",
  "currency": "DOP",
  "payment_method": "cash",
  "status": "paid",
  "transaction_reference": "RCPT-0001",
  "notes": "Deposito inicial"
}
```

Errores esperados:

- `400 bad_request`: cita cancelada.
- `403 forbidden`: barbero intentando gestionar pago de otra cita.
- `404 not_found`: cita inexistente.
- `422 validation_error`: monto menor o igual a cero, estado o metodo invalido.

## 18. Listar Pagos de una Cita

```http
GET /payments/appointment/<APPOINTMENT_ID>
Authorization: Bearer <TOKEN>
```

## 19. Marcar Pago Pendiente como Cobrado

```http
PATCH /payments/<PAYMENT_ID>/mark-paid
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

```json
{
  "transaction_reference": "AUTH-12345",
  "notes": "Pago confirmado"
}
```

## 20. Reembolsar Pago

```http
PATCH /payments/<PAYMENT_ID>/refund
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

```json
{
  "reason": "Cliente solicito reembolso"
}
```

## 21. Resumen de Pagos

Requiere admin.

```http
GET /payments/summary?currency=DOP
Authorization: Bearer <ADMIN_TOKEN>
```

Response:

```json
{
  "total_payments": 2,
  "total_paid": 1000.0,
  "total_refunded": 250.0,
  "currency": "DOP"
}
```

## 22. Caja

Abrir caja:

```http
POST /cash-sessions/open
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

```json
{
  "branch_id": 1,
  "opening_amount": "1000.00",
  "notes": "Apertura del turno"
}
```

Crear movimiento manual:

```http
POST /cash-movements/
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

```json
{
  "cash_session_id": 1,
  "movement_type": "expense",
  "amount": "150.00",
  "method": "cash",
  "description": "Compra de insumos"
}
```

Cerrar caja:

```http
PATCH /cash-sessions/1/close
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

```json
{
  "closing_amount": "1850.00",
  "notes": "Cierre sin novedad"
}
```

Reglas:

- Pagos `cash` crean `income` automaticamente si hay caja abierta en la sucursal.
- Reembolsos `cash` crean `refund`.
- No se duplican movimientos automaticos por `payment_id`.
- Sin caja abierta, un pago `cash` de una cita con sucursal retorna `409 conflict`.

## 23. Comisiones de Barberos

Crear regla porcentual:

```http
POST /commissions/rules
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

```json
{
  "barber_id": 2,
  "branch_id": 1,
  "service_id": null,
  "commission_type": "percentage",
  "commission_value": "10.00"
}
```

Crear regla fija por servicio:

```http
POST /commissions/rules
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

```json
{
  "barber_id": 2,
  "branch_id": 1,
  "service_id": 3,
  "commission_type": "fixed",
  "commission_value": "150.00"
}
```

Listar comisiones:

```http
GET /commissions/?status=pending
Authorization: Bearer <TOKEN>
```

Aprobar y marcar pagada:

```http
PATCH /commissions/<COMMISSION_ID>/approve
Authorization: Bearer <ADMIN_TOKEN>
```

```http
PATCH /commissions/<COMMISSION_ID>/mark-paid
Authorization: Bearer <ADMIN_TOKEN>
```

Resumen:

```http
GET /commissions/summary?start_date=2026-05-01&end_date=2026-05-31
Authorization: Bearer <ADMIN_TOKEN>
```

Response:

```json
{
  "start_date": "2026-05-01",
  "end_date": "2026-05-31",
  "by_status": {
    "pending": {
      "count": 3,
      "total": 750.0
    }
  },
  "by_barber": [
    {
      "barber_id": 2,
      "total": 500.0
    }
  ],
  "by_branch": [
    {
      "branch_id": 1,
      "total": 500.0
    }
  ]
}
```

Reglas:

- Las reglas por servicio tienen prioridad sobre las reglas por sucursal o globales del barbero.
- Los pagos `paid` y `partially_paid` generan comision si existe una regla activa.
- No se duplica comision para el mismo `payment_id`.
- Reembolsar un pago cancela la comision pendiente o aprobada.
- Admin gestiona reglas y estados; barber solo ve sus comisiones.

## 24. Penalizaciones y Reputacion del Cliente

Listar penalizaciones de un cliente:

```http
GET /clients/<CLIENT_ID>/penalties
Authorization: Bearer <TOKEN>
```

Crear penalizacion manual:

```http
POST /clients/<CLIENT_ID>/penalties
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

```json
{
  "appointment_id": 10,
  "penalty_type": "manual",
  "reason": "Incumplimiento recurrente",
  "amount": "100.00",
  "points": 1
}
```

Perdonar, cobrar o cancelar:

```http
PATCH /penalties/<PENALTY_ID>/forgive
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

```json
{
  "reason": "Cortesia comercial"
}
```

```http
PATCH /penalties/<PENALTY_ID>/mark-paid
Authorization: Bearer <ADMIN_TOKEN>
```

```http
PATCH /penalties/<PENALTY_ID>/cancel
Authorization: Bearer <ADMIN_TOKEN>
```

Mis penalizaciones:

```http
GET /me/penalties
Authorization: Bearer <TOKEN_CLIENT>
```

Reporte:

```http
GET /reports/clients/penalties?start_date=2026-05-01&end_date=2026-05-31
Authorization: Bearer <ADMIN_TOKEN>
```

Response:

```json
{
  "by_status": [
    {
      "status": "active",
      "count": 4,
      "amount": 300.0,
      "points": 8
    }
  ],
  "top_no_show_clients": [
    {
      "client_id": 1,
      "no_shows": 2,
      "points": 6
    }
  ],
  "by_branch": [
    {
      "branch_id": 1,
      "count": 3,
      "amount": 200.0,
      "points": 5
    }
  ]
}
```

Reglas:

- `PATCH /appointments/<APPOINTMENT_ID>/no-show` genera penalizacion `no_show`.
- Cancelar tarde como cliente genera penalizacion `late_cancel` si hay puntos o monto configurado.
- Si el cliente supera `CLIENT_MAX_ACTIVE_PENALTY_POINTS` y `CLIENT_BLOCK_BOOKING_ON_PENALTY=true`, no puede crear nuevas citas.
- Admin gestiona todas las penalizaciones; barber ve penalizaciones relacionadas con sus citas; client solo ve las propias.

## 25. Inventario y Ventas POS

Crear producto:

```http
POST /products/
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

```json
{
  "branch_id": 1,
  "name": "Pomada mate",
  "description": "Pomada de fijacion media",
  "sku": "POM-MATE-001",
  "barcode": "750000000001",
  "category": "Styling",
  "brand": "BarberPro",
  "cost_price": "200.00",
  "sale_price": "450.00",
  "stock_quantity": 10,
  "min_stock_alert": 3
}
```

Movimiento de inventario:

```http
POST /inventory/movements
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

```json
{
  "product_id": 1,
  "movement_type": "purchase",
  "quantity": 5,
  "unit_cost": "200.00",
  "reference_type": "manual",
  "reference_id": null
}
```

Registrar venta de producto:

```http
POST /product-sales/
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

```json
{
  "product_id": 1,
  "branch_id": 1,
  "client_id": 10,
  "quantity": 2,
  "unit_price": "450.00",
  "payment_method": "cash"
}
```

Consultar stock bajo:

```http
GET /products/low-stock?branch_id=1
Authorization: Bearer <TOKEN>
```

Reporte de productos:

```http
GET /reports/products?start_date=2026-05-01&end_date=2026-05-31
Authorization: Bearer <ADMIN_TOKEN>
```

Response:

```json
{
  "top_products": [
    {
      "product_id": 1,
      "product": "Pomada mate",
      "quantity": 12,
      "income": 5400.0
    }
  ],
  "by_branch": [
    {
      "branch_id": 1,
      "income": 5400.0,
      "cost": 2400.0,
      "margin": 3000.0
    }
  ]
}
```

Reglas:

- SKU es unico.
- Ventas descuentan stock y registran movimiento `sale`.
- `refund` devuelve stock.
- Producto inactivo no puede venderse.
- Venta `cash` con sucursal requiere caja abierta y crea movimiento `income`.
- Admin gestiona todo; barber vende y consulta stock de su sucursal; client no administra inventario.

## 26. Dashboard para Frontend

Todos los endpoints aceptan:

- `start_date`
- `end_date`
- `branch_id` opcional
- `barber_id` opcional

Overview:

```http
GET /dashboard/overview?start_date=2026-05-01&end_date=2026-05-31
Authorization: Bearer <TOKEN>
```

Response:

```json
{
  "totals": {
    "total_appointments": 120,
    "completed_appointments": 95,
    "cancelled_appointments": 10,
    "no_show_appointments": 5,
    "total_revenue": 85000.0,
    "total_refunds": 2500.0,
    "net_revenue": 82500.0,
    "pending_payments": 8,
    "active_clients": 230,
    "new_clients": 18
  },
  "top_services": [
    {
      "id": 1,
      "label": "Corte",
      "value": 60
    }
  ],
  "top_barbers": [
    {
      "id": 2,
      "label": "barber@test.com",
      "value": 45
    }
  ],
  "upcoming_appointments_today": []
}
```

Financiero:

```http
GET /dashboard/financial?start_date=2026-05-01&end_date=2026-05-31&branch_id=1
Authorization: Bearer <TOKEN>
```

Incluye `revenue_by_day`, `revenue_by_month`, `revenue_by_payment_method`, `revenue_by_branch`, `revenue_by_barber`, totales por metodo, `refunds`, `net_revenue`, `pending_balances`, `commissions_pending` y `commissions_paid`.

Citas:

```http
GET /dashboard/appointments?start_date=2026-05-01&end_date=2026-05-31
Authorization: Bearer <TOKEN>
```

Incluye estados, series por dia/hora, tasas de cancelacion/no-show, promedio diario y horas/dias mas ocupados.

Barberos, clientes y sucursales:

```http
GET /dashboard/barbers?start_date=2026-05-01&end_date=2026-05-31
GET /dashboard/clients?start_date=2026-05-01&end_date=2026-05-31
GET /dashboard/branches?start_date=2026-05-01&end_date=2026-05-31
Authorization: Bearer <TOKEN>
```

Reglas:

- Admin ve metricas globales y puede filtrar.
- Barber solo ve sus propias metricas y su sucursal.
- Client recibe `403 forbidden`.
- Los ingresos se calculan desde `payments` con estado `paid` o `partially_paid`.

## 27. Notificaciones y Recordatorios

Listar notificaciones:

```http
GET /notifications/
Authorization: Bearer <TOKEN>
```

Response:

```json
[
  {
    "id": 1,
    "recipient_type": "barber",
    "recipient_id": 2,
    "channel": "in_app",
    "subject": "appointment_created",
    "message": "Cita creada: cita #1 para el 2026-06-01 a las 10:00:00.",
    "status": "pending",
    "related_type": "appointment",
    "related_id": 1,
    "scheduled_for": null,
    "sent_at": null,
    "failed_at": null,
    "error_message": null,
    "created_at": "2026-06-01T10:00:00Z",
    "updated_at": "2026-06-01T10:00:00Z"
  }
]
```

Marcar como enviada:

```http
PATCH /notifications/<NOTIFICATION_ID>/mark-sent
Authorization: Bearer <TOKEN>
```

Marcar como fallida:

```http
PATCH /notifications/<NOTIFICATION_ID>/mark-failed
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

```json
{
  "error_message": "Proveedor externo no disponible"
}
```

Cancelar notificacion:

```http
PATCH /notifications/<NOTIFICATION_ID>/cancel
Authorization: Bearer <TOKEN>
```

Generar recordatorios pendientes:

```http
POST /notifications/generate-reminders
Authorization: Bearer <ADMIN_TOKEN>
```

Response:

```json
{
  "created": 2
}
```

Reglas:

- Admin ve todas las notificaciones.
- Barbero ve notificaciones propias o relacionadas con sus citas.
- Los recordatorios se crean como `pending`; no se envia email, SMS ni WhatsApp todavia.
- No se duplican recordatorios para la misma cita, ventana y fecha programada.

## 28. Reportes Financieros

Los reportes financieros usan pagos reales, no el precio teorico de la cita.

```http
GET /reports/dashboard?start_date=2026-06-01&end_date=2026-06-30
Authorization: Bearer <ADMIN_TOKEN>
```

Response:

```json
{
  "total": 10,
  "agendadas": 2,
  "confirmada": 3,
  "completadas": 4,
  "canceladas": 1,
  "no_show": 0,
  "ingresos": 5000.0,
  "total_reembolsado": 500.0,
  "balance_neto": 4500.0,
  "no_show_rate": 0
}
```

Ingresos por barbero:

```http
GET /reports/financial/by-barber?start_date=2026-06-01&end_date=2026-06-30
Authorization: Bearer <TOKEN>
```

Admin ve todos. Barbero solo ve sus propios ingresos.

Ingresos por metodo de pago:

```http
GET /reports/financial/by-method?start_date=2026-06-01&end_date=2026-06-30
Authorization: Bearer <ADMIN_TOKEN>
```

```json
[
  {
    "payment_method": "cash",
    "payments": 12,
    "ingresos": 6000.0
  }
]
```

Citas con saldo pendiente:

```http
GET /reports/financial/pending-balances?start_date=2026-06-01&end_date=2026-06-30
Authorization: Bearer <TOKEN>
```

Exportar pagos:

```http
GET /reports/financial/by-barber/export/csv?start_date=2026-06-01&end_date=2026-06-30
Authorization: Bearer <ADMIN_TOKEN>
```

Columnas del export:

```text
fecha,cita,cliente,barbero,servicio,metodo_pago,monto_pagado,monto_reembolsado,balance_neto,estado_pago
```

Reglas financieras:

- `paid` y `partially_paid` suman como ingreso cobrado.
- `refunded` se reporta como reembolso.
- `pending`, `failed` y `cancelled` no suman ingresos.
- `balance_neto = ingresos - reembolsos`.

Ingresos por sucursal:

```http
GET /reports/financial/by-branch?start_date=2026-06-01&end_date=2026-06-30
Authorization: Bearer <ADMIN_TOKEN>
```

```json
[
  {
    "branch_id": 1,
    "branch": "Sucursal Centro",
    "ingresos": 5000.0
  }
]
```

## 29. Reportes Operativos

Demanda por hora:

```http
GET /reports/operations/hours?start_date=2026-06-01&end_date=2026-06-30
Authorization: Bearer <ADMIN_TOKEN>
```

```json
[
  {
    "hour": "10:00",
    "total": 8
  }
]
```

Demanda por dia de semana:

```http
GET /reports/operations/days?start_date=2026-06-01&end_date=2026-06-30
Authorization: Bearer <ADMIN_TOKEN>
```

```json
[
  {
    "weekday": "Monday",
    "total": 12
  }
]
```

Estos reportes son compatibles con PostgreSQL en produccion y SQLite en tests.

## 30. Ver Historial

```http
GET /appointments/<APPOINTMENT_ID>/history
Authorization: Bearer <TOKEN>
```

Response:

```json
[
  {
    "id": 1,
    "appointment_id": 1,
    "action": "created",
    "old_values": null,
    "new_values": {
      "status": "agendada"
    },
    "changed_by_user_id": 1,
    "reason": null,
    "created_at": "2026-06-01T10:00:00Z"
  }
]
```

## 31. Formato de Error Estandar

```json
{
  "success": false,
  "message": "Horario no disponible",
  "error_code": "conflict",
  "details": {},
  "request_id": "4f0c2d9e-..."
}
```
