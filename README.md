# BARBER_AGENDA API

BARBER_AGENDA es una API REST para gestionar una barberia: usuarios, barberos, clientes, servicios, citas, disponibilidad real por barbero, bloqueos de agenda, cancelaciones, reprogramaciones, historial de cambios, pagos/depositos, caja, comisiones para barberos, inventario, ventas de productos, dashboards para frontend, notificaciones internas y reportes operativos.

La API esta construida con una arquitectura por capas:

```text
API routers -> Services -> Repositories -> SQLAlchemy models -> PostgreSQL
```

## Stack Tecnico

- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic
- JWT con `python-jose`
- bcrypt/passlib para passwords
- Pytest

## Requisitos

- Windows 10/11
- Python instalado y disponible como `python`
- PostgreSQL instalado localmente
- `psql.exe` disponible por ruta completa o agregado al PATH
- Git, opcional

Ruta tipica de PostgreSQL en Windows:

```powershell
C:\Program Files\PostgreSQL\16\bin
```

## Instalacion en Windows

Desde PowerShell:

```powershell
cd C:\Users\HOLA\Escritorio\barber_agenda
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloquea la activacion del entorno:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Configuracion

Copia `.env.example` a `.env`:

```powershell
Copy-Item .env.example .env
```

Edita `.env` con tus valores locales.

Variables soportadas:

| Variable | Descripcion |
| --- | --- |
| `DATABASE_URL` | URL SQLAlchemy de PostgreSQL. |
| `SECRET_KEY` | Secreto para firmar JWT. Debe ser largo y privado. |
| `ENVIRONMENT` | `development`, `test` o `production`. |
| `JWT_ALGORITHM` | Algoritmo JWT. Valor recomendado: `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duracion del token de acceso. |
| `CORS_ALLOWED_ORIGINS` | Lista separada por comas de origins permitidos. |
| `ALLOWED_HOSTS` | Lista separada por comas para TrustedHostMiddleware. |
| `LOGIN_RATE_LIMIT_REQUESTS` | Intentos permitidos por ventana en login. |
| `LOGIN_RATE_LIMIT_WINDOW_SECONDS` | Ventana del rate limit de login. |
| `CLIENT_CANCEL_CUTOFF_HOURS` | Horas minimas de anticipacion para que un cliente cancele. |
| `CLIENT_RESCHEDULE_CUTOFF_HOURS` | Horas minimas de anticipacion para que un cliente reprograme. |

Ejemplo:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/barberdb
SECRET_KEY=change-this-local-secret
ENVIRONMENT=development
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ALLOWED_HOSTS=localhost,127.0.0.1,testserver
LOGIN_RATE_LIMIT_REQUESTS=5
LOGIN_RATE_LIMIT_WINDOW_SECONDS=60
CLIENT_CANCEL_CUTOFF_HOURS=24
CLIENT_RESCHEDULE_CUTOFF_HOURS=24
CLIENT_MAX_ACTIVE_PENALTY_POINTS=5
CLIENT_BLOCK_BOOKING_ON_PENALTY=true
CLIENT_NO_SHOW_PENALTY_POINTS=3
CLIENT_NO_SHOW_PENALTY_AMOUNT=0
CLIENT_LATE_CANCEL_PENALTY_POINTS=1
CLIENT_LATE_CANCEL_PENALTY_AMOUNT=0
```

## Base de Datos y Migraciones

Crear base limpia:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d postgres -c "CREATE DATABASE barberdb;"
```

Aplicar migraciones:

```powershell
venv\Scripts\python.exe -m alembic upgrade head
```

Ver revision actual:

```powershell
venv\Scripts\python.exe -m alembic current
```

Ver head disponible:

```powershell
venv\Scripts\python.exe -m alembic heads
```

## Ejecutar Servidor

```powershell
venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

URLs utiles:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Ejecutar Tests

```powershell
venv\Scripts\python.exe -m pytest -q
```

## Flujo Recomendado de Desarrollo

1. Crear o actualizar rama de trabajo.
2. Actualizar modelos/schemas/services/repos segun el cambio.
3. Crear migracion Alembic si cambia la base de datos.
4. Ejecutar `alembic upgrade head`.
5. Agregar o actualizar tests.
6. Ejecutar `pytest -q`.
7. Probar manualmente en Swagger o con los ejemplos en `docs/api_examples.md`.

## Modulos Principales

### Auth

- Crear primer admin: `POST /api/v1/auth/register`
- Login: `POST /api/v1/auth/login`
- Crear barbero: `POST /api/v1/auth/barbers`
- Registrar cliente autenticado: `POST /api/v1/auth/register-client`

El registro de cliente crea un `User` con `role=client` y lo asocia a un `Client` mediante `users.client_id`. Los clientes existentes sin usuario siguen siendo validos para operaciones internas.

### Usuarios y Barberos

- Autoservicio actual: `GET /api/v1/me`
- Mis citas: `GET /api/v1/me/appointments`
- Mis pagos: `GET /api/v1/me/payments`
- Mis notificaciones: `GET /api/v1/me/notifications`
- Mis penalizaciones: `GET /api/v1/me/penalties`
- Editar perfil cliente: `PATCH /api/v1/me/client-profile`
- Perfil actual: `GET /api/v1/users/me`
- Listar usuarios: `GET /api/v1/users/`
- Actualizar usuario: `PUT /api/v1/users/{user_id}`
- Desactivar usuario: `DELETE /api/v1/users/{user_id}/deactivate`

Permisos de cliente autenticado:

- Puede crear citas solo para su propio `client_id`.
- Puede ver, cancelar, reprogramar y consultar historial de sus propias citas.
- Puede ver sus pagos y notificaciones propias.
- No puede ver reportes admin ni gestionar horarios, bloqueos o pagos.
- No puede cancelar/reprogramar dentro de la ventana configurada por `CLIENT_CANCEL_CUTOFF_HOURS` y `CLIENT_RESCHEDULE_CUTOFF_HOURS`.

`clients.phone` es unico. Antes de aplicar la migracion que agrega `uq_clients_phone`, revisa duplicados en PostgreSQL:

```sql
SELECT phone, COUNT(*)
FROM clients
WHERE phone IS NOT NULL
GROUP BY phone
HAVING COUNT(*) > 1;
```

### Clientes

- Crear cliente: `POST /api/v1/clients/`
- Listar clientes: `GET /api/v1/clients/`
- Actualizar cliente: `PUT /api/v1/clients/{client_id}`

### Sucursales

- Crear sucursal: `POST /api/v1/branches/`
- Listar sucursales: `GET /api/v1/branches/`
- Ver sucursal: `GET /api/v1/branches/{branch_id}`
- Actualizar sucursal: `PUT /api/v1/branches/{branch_id}`
- Desactivar sucursal: `DELETE /api/v1/branches/{branch_id}`
- Ver configuracion de sucursal: `GET /api/v1/branches/{branch_id}/settings`
- Actualizar configuracion de sucursal: `PUT /api/v1/branches/{branch_id}/settings`

Las sucursales se relacionan con:

- Barberos mediante `users.branch_id`.
- Servicios mediante `services.branch_id`.
- Citas mediante `appointments.branch_id`.

`branch_id` es opcional para compatibilidad con datos existentes. Si se usa, la API valida que el barbero y el servicio pertenezcan a la sucursal seleccionada.

La configuracion por sucursal permite definir:

- timezone
- currency
- horas limite para cancelar/reprogramar
- deposito requerido, monto o porcentaje por defecto
- recordatorios 24h y 2h habilitados/deshabilitados

Si una cita no tiene sucursal o la sucursal no tiene settings, la API usa la configuracion global de `.env` como fallback.

### Servicios

- Crear servicio: `POST /api/v1/services/`
- Listar servicios: `GET /api/v1/services/`
- Listar servicios por sucursal: `GET /api/v1/services/?branch_id=1`
- Actualizar servicio: `PUT /api/v1/services/{service_id}`

### Citas

- Crear cita: `POST /api/v1/appointments/`
- Consultar disponibilidad: `GET /api/v1/appointments/available-slots`
- Consultar disponibilidad por sucursal: `GET /api/v1/appointments/available-slots?branch_id=1&barber_id=2&service_id=1&date=2026-06-01`
- Confirmar: `PATCH /api/v1/appointments/{appointment_id}/confirm`
- Completar: `PATCH /api/v1/appointments/{appointment_id}/complete`
- Marcar no-show: `PATCH /api/v1/appointments/{appointment_id}/no-show`
- Reprogramar: `PATCH /api/v1/appointments/{appointment_id}/reschedule`
- Cancelar: `PATCH /api/v1/appointments/{appointment_id}/cancel`
- Historial: `GET /api/v1/appointments/{appointment_id}/history`

### Pagos y Depositos

- Crear pago/deposito: `POST /api/v1/payments/`
- Ver pago: `GET /api/v1/payments/{payment_id}`
- Pagos de una cita: `GET /api/v1/payments/appointment/{appointment_id}`
- Marcar pago como cobrado: `PATCH /api/v1/payments/{payment_id}/mark-paid`
- Reembolsar pago: `PATCH /api/v1/payments/{payment_id}/refund`
- Resumen financiero: `GET /api/v1/payments/summary`

Estados soportados: `pending`, `paid`, `partially_paid`, `refunded`, `failed`, `cancelled`.

Metodos soportados: `cash`, `card`, `transfer`, `online`, `other`.

### Caja

- Abrir caja: `POST /api/v1/cash-sessions/open`
- Cerrar caja: `PATCH /api/v1/cash-sessions/{session_id}/close`
- Caja abierta actual: `GET /api/v1/cash-sessions/current?branch_id=1`
- Ver caja: `GET /api/v1/cash-sessions/{session_id}`
- Crear movimiento manual: `POST /api/v1/cash-movements/`
- Listar movimientos: `GET /api/v1/cash-movements/session/{session_id}`

Reglas:

- Solo puede haber una caja abierta por sucursal.
- Pagos `cash` con estado cobrado crean movimiento `income`.
- Reembolsos `cash` crean movimiento `refund`.
- No se permiten movimientos en caja cerrada.
- Al cerrar caja se calcula `expected_amount` y `difference_amount`.
- Admin gestiona todas las cajas; barber solo caja de su sucursal.

### Comisiones

- Crear regla: `POST /api/v1/commissions/rules`
- Listar reglas: `GET /api/v1/commissions/rules`
- Actualizar regla: `PUT /api/v1/commissions/rules/{rule_id}`
- Desactivar regla: `PATCH /api/v1/commissions/rules/{rule_id}/deactivate`
- Listar comisiones: `GET /api/v1/commissions/`
- Comisiones por barbero: `GET /api/v1/commissions/barber/{barber_id}`
- Aprobar comision: `PATCH /api/v1/commissions/{commission_id}/approve`
- Marcar comision pagada: `PATCH /api/v1/commissions/{commission_id}/mark-paid`
- Resumen: `GET /api/v1/commissions/summary?start_date=2026-05-01&end_date=2026-05-31`

Reglas:

- Admin gestiona reglas, aprobaciones y pagos de comisiones.
- Barber solo consulta sus propias comisiones.
- Al registrar un pago `paid` o `partially_paid`, la API genera una comision si hay regla activa aplicable.
- La regla por servicio tiene prioridad; si no existe, se usa la regla por barbero/sucursal o barbero global.
- Cada pago puede generar como maximo una comision.
- Al reembolsar un pago, la comision pendiente/aprobada se cancela.

### Penalizaciones y Reputacion

- Penalizaciones de cliente: `GET /api/v1/clients/{client_id}/penalties`
- Crear penalizacion manual: `POST /api/v1/clients/{client_id}/penalties`
- Perdonar penalizacion: `PATCH /api/v1/penalties/{penalty_id}/forgive`
- Marcar penalizacion pagada: `PATCH /api/v1/penalties/{penalty_id}/mark-paid`
- Cancelar penalizacion: `PATCH /api/v1/penalties/{penalty_id}/cancel`
- Mis penalizaciones: `GET /api/v1/me/penalties`
- Reporte: `GET /api/v1/reports/clients/penalties`

Reglas:

- Marcar una cita como `no_show` genera una penalizacion automatica y una notificacion interna al cliente.
- Una cancelacion tardia de cliente dentro de la ventana de corte genera penalizacion `late_cancel` antes de rechazar la cancelacion.
- `CLIENT_MAX_ACTIVE_PENALTY_POINTS` define el limite de puntos activos permitido.
- `CLIENT_BLOCK_BOOKING_ON_PENALTY=true` bloquea nuevas reservas si el cliente supera el limite.
- BranchSettings puede sobrescribir puntos y montos de penalizacion por no-show y cancelacion tardia.
- Admin gestiona todas; barber ve las relacionadas con sus citas; client solo ve las propias.

### Inventario y Ventas POS

- Crear producto: `POST /api/v1/products/`
- Listar productos: `GET /api/v1/products/?branch_id=1`
- Ver producto: `GET /api/v1/products/{product_id}`
- Actualizar producto: `PUT /api/v1/products/{product_id}`
- Desactivar producto: `PATCH /api/v1/products/{product_id}/deactivate`
- Stock bajo: `GET /api/v1/products/low-stock`
- Crear movimiento: `POST /api/v1/inventory/movements`
- Listar movimientos: `GET /api/v1/inventory/movements`
- Registrar venta: `POST /api/v1/product-sales/`
- Listar ventas: `GET /api/v1/product-sales/`
- Reporte de productos: `GET /api/v1/reports/products`

Reglas:

- SKU es unico.
- El stock no puede quedar negativo.
- Las ventas descuentan stock y crean movimiento `sale`.
- Movimientos manuales `purchase`, `adjustment`, `loss` y `refund` ajustan stock con auditoria.
- Productos inactivos no pueden venderse.
- Ventas `cash` en sucursal requieren caja abierta y crean movimiento de caja `income`.
- Admin gestiona inventario; barber puede vender y consultar stock de su sucursal; client no administra inventario.

### Dashboard Frontend

Todos aceptan `start_date`, `end_date`, `branch_id` opcional y `barber_id` opcional:

- General: `GET /api/v1/dashboard/overview`
- Financiero: `GET /api/v1/dashboard/financial`
- Citas: `GET /api/v1/dashboard/appointments`
- Barberos: `GET /api/v1/dashboard/barbers`
- Clientes: `GET /api/v1/dashboard/clients`
- Sucursales: `GET /api/v1/dashboard/branches`

Reglas:

- Admin puede consultar dashboard global y filtrar por sucursal o barbero.
- Barber queda limitado a sus propias metricas y su sucursal.
- Client no puede acceder al dashboard.
- Los ingresos usan `payments` cobrados como fuente real.
- Las respuestas estan preparadas para frontend con `totals`, `series`, `label`, `value`, `percentages` y listas de comparacion.

### Notificaciones y Recordatorios

- Listar notificaciones: `GET /api/v1/notifications/`
- Ver notificacion: `GET /api/v1/notifications/{notification_id}`
- Marcar enviada: `PATCH /api/v1/notifications/{notification_id}/mark-sent`
- Marcar fallida: `PATCH /api/v1/notifications/{notification_id}/mark-failed`
- Cancelar notificacion: `PATCH /api/v1/notifications/{notification_id}/cancel`
- Generar recordatorios pendientes: `POST /api/v1/notifications/generate-reminders`

Canales soportados: `email`, `sms`, `whatsapp`, `in_app`.

Estados soportados: `pending`, `sent`, `failed`, `cancelled`.

La API crea notificaciones internas `pending` para eventos de cita, pagos y reembolsos. Los recordatorios se generan para 24 horas y 2 horas antes de la cita, sin enviar todavia a proveedores externos.

### Horarios por Barbero

- Crear horario: `POST /api/v1/barber-schedules/`
- Listar horarios: `GET /api/v1/barber-schedules/barber/{barber_id}`
- Actualizar horario: `PUT /api/v1/barber-schedules/{schedule_id}`
- Activar/desactivar: `PATCH /api/v1/barber-schedules/{schedule_id}/activate`

### Bloqueos

- Crear bloqueo: `POST /api/v1/barber-time-blocks/`
- Listar bloqueos: `GET /api/v1/barber-time-blocks/`
- Actualizar bloqueo: `PUT /api/v1/barber-time-blocks/{block_id}`
- Desactivar bloqueo: `DELETE /api/v1/barber-time-blocks/{block_id}`

### Reportes

- Dashboard: `GET /api/v1/reports/dashboard`
- Ingresos por barbero: `GET /api/v1/reports/financial/by-barber`
- Ingresos por servicio: `GET /api/v1/reports/financial/by-service`
- Ingresos por sucursal: `GET /api/v1/reports/financial/by-branch`
- Ingresos por metodo de pago: `GET /api/v1/reports/financial/by-method`
- Ingresos diarios: `GET /api/v1/reports/financial/daily`
- Ingresos mensuales: `GET /api/v1/reports/financial/monthly`
- Citas con saldo pendiente: `GET /api/v1/reports/financial/pending-balances`
- Export CSV de pagos: `GET /api/v1/reports/financial/by-barber/export/csv`
- Export Excel de pagos: `GET /api/v1/reports/financial/by-barber/export/excel`
- Clientes frecuentes: `GET /api/v1/reports/clients/frequent`
- No-shows: `GET /api/v1/reports/clients/no-show`
- Penalizaciones: `GET /api/v1/reports/clients/penalties`
- Productos: `GET /api/v1/reports/products`
- Demanda por hora: `GET /api/v1/reports/operations/hours`
- Demanda por dia de semana: `GET /api/v1/reports/operations/days`

Los reportes financieros usan `payments` como fuente real:

- Suman pagos con `status` `paid` o `partially_paid`.
- Excluyen `pending`, `failed` y `cancelled`.
- Reportan `refunded` separado y calculan `balance_neto = ingresos - reembolsos`.
- Admin ve todos los ingresos; barbero ve solo sus propias citas en reportes habilitados para su rol.

Los reportes operativos de demanda usan expresiones compatibles por motor:

- PostgreSQL: `to_char` y `extract`.
- SQLite en tests: `strftime`.

## Formato de Errores

Los errores siguen este formato:

```json
{
  "success": false,
  "message": "Usuario no encontrado",
  "error_code": "not_found",
  "details": {},
  "request_id": "..."
}
```

Codigos comunes:

- `400 bad_request`
- `401 unauthorized`
- `403 forbidden`
- `404 not_found`
- `409 conflict`
- `422 validation_error`
- `429 rate_limited`
- `500 internal_error`

## Notas de Produccion

- No usar `SECRET_KEY` de ejemplo.
- No usar `*` en CORS ni hosts permitidos en produccion.
- Usar PostgreSQL real para validar constraints GiST.
- Migrar `rate_limit` en memoria a Redis si hay multiples workers.
