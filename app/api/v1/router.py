from fastapi import APIRouter
from app.api.v1 import auth, users, clients, services, appointments, reports, payments, notifications, me, branches, cash_register, commissions, penalties, products, inventory, product_sales, dashboard
from app.api.v1 import barber_schedules, barber_time_blocks

api_router = APIRouter()

openapi_tags = [
    {
        "name": "Auth",
        "description": "Registro del primer admin, login JWT y creacion de barberos.",
    },
    {
        "name": "Users",
        "description": "Usuarios del sistema, perfil actual, roles y activacion.",
    },
    {
        "name": "Clients",
        "description": "Clientes de la barberia y soft delete.",
    },
    {
        "name": "Services",
        "description": "Servicios ofrecidos, duracion, precio y activacion.",
    },
    {
        "name": "Appointments",
        "description": "Citas, disponibilidad, estados, cancelacion, reprogramacion e historial.",
    },
    {
        "name": "Barber schedules",
        "description": "Disponibilidad semanal, descansos y horarios activos por barbero.",
    },
    {
        "name": "Barber time blocks",
        "description": "Bloqueos de agenda por fecha, dia completo o rango parcial.",
    },
    {
        "name": "Reports",
        "description": "Metricas operativas, financieras y exportaciones.",
    },
    {
        "name": "Payments",
        "description": "Pagos, depositos, reembolsos y resumen financiero interno.",
    },
    {
        "name": "Notifications",
        "description": "Notificaciones internas, estados de envio y recordatorios pendientes.",
    },
    {
        "name": "Me",
        "description": "Autoservicio para el usuario autenticado.",
    },
    {
        "name": "Branches",
        "description": "Sucursales, asignacion operativa y filtros por ubicacion.",
    },
    {
        "name": "Cash register",
        "description": "Sesiones de caja y movimientos financieros por sucursal.",
    },
    {
        "name": "Commissions",
        "description": "Reglas y comisiones generadas para barberos por pagos cobrados.",
    },
    {
        "name": "Penalties",
        "description": "Penalizaciones, no-show, cancelaciones tardias y reputacion del cliente.",
    },
    {
        "name": "Inventory",
        "description": "Productos, movimientos de inventario y ventas POS.",
    },
    {
        "name": "Dashboard",
        "description": "Agregados listos para frontend: negocio, finanzas, citas, barberos, clientes y sucursales.",
    },
]

api_router.include_router(me.router, tags=["Me"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(clients.router, prefix="/clients", tags=["Clients"])
api_router.include_router(branches.router, prefix="/branches", tags=["Branches"])
api_router.include_router(services.router, prefix="/services", tags=["Services"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
api_router.include_router(barber_schedules.router, prefix="/barber-schedules", tags=["Barber schedules"])
api_router.include_router(barber_time_blocks.router, prefix="/barber-time-blocks", tags=["Barber time blocks"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(commissions.router, prefix="/commissions", tags=["Commissions"])
api_router.include_router(penalties.router, prefix="/penalties", tags=["Penalties"])
api_router.include_router(products.router, prefix="/products", tags=["Inventory"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
api_router.include_router(product_sales.router, prefix="/product-sales", tags=["Inventory"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(cash_register.router)
api_router.include_router(reports.router)
