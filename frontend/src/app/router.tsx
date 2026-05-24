import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";
import { AuthBootstrap } from "@/components/layout/AuthBootstrap";
import { AppShell } from "@/components/layout/AppShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { LoginPage } from "@/features/auth/LoginPage";
import { ClientDashboardPage } from "@/features/dashboard/ClientDashboardPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { ForbiddenPage } from "@/features/errors/ForbiddenPage";
import { PlaceholderPage } from "@/features/placeholders/PlaceholderPage";

const placeholder = (title: string, description: string) => (
  <PlaceholderPage title={title} description={description} />
);

function RootRoute() {
  return (
    <>
      <AuthBootstrap />
      <Outlet />
    </>
  );
}

export const router = createBrowserRouter([
  {
    element: <RootRoute />,
    children: [
      {
        path: "/",
        element: <Navigate to="/app/dashboard" replace />
      },
      {
        path: "/login",
        element: <LoginPage />
      },
      {
        path: "/forbidden",
        element: <ForbiddenPage />
      },
      {
        element: <RoleGuard roles={["admin", "barber", "client"]} />,
        children: [
          {
            path: "/app",
            element: <AppShell />,
            children: [
              { index: true, element: <Navigate to="/app/dashboard" replace /> },
              {
                element: <RoleGuard roles={["admin", "barber"]} />,
                children: [
                  { path: "dashboard", element: <DashboardPage /> },
                  { path: "calendar", element: placeholder("Agenda", "Calendario y gestion de citas.") },
                  { path: "clients", element: placeholder("Clientes", "Listado y detalle de clientes.") },
                  { path: "payments", element: placeholder("Pagos", "Pagos, depositos y reembolsos.") },
                  { path: "cash", element: placeholder("Caja", "Sesion de caja y movimientos.") },
                  { path: "notifications", element: placeholder("Notificaciones", "Bandeja de notificaciones internas.") }
                ]
              },
              {
                element: <RoleGuard roles={["admin"]} />,
                children: [
                  { path: "barbers", element: placeholder("Barberos", "Usuarios barberos, horarios y bloqueos.") },
                  { path: "services", element: placeholder("Servicios", "Catalogo de servicios.") },
                  { path: "branches", element: placeholder("Sucursales", "Sucursales y configuracion por sede.") },
                  { path: "commissions", element: placeholder("Comisiones", "Reglas y liquidacion de comisiones.") },
                  { path: "inventory", element: placeholder("Inventario", "Productos, stock y movimientos.") },
                  { path: "reports", element: placeholder("Reportes", "Reportes financieros y operativos.") },
                  { path: "settings", element: placeholder("Configuracion", "Parametros operativos del sistema.") }
                ]
              },
              {
                element: <RoleGuard roles={["barber"]} />,
                children: [
                  { path: "my-commissions", element: placeholder("Mis comisiones", "Consulta de comisiones propias.") },
                  { path: "pos", element: placeholder("POS", "Venta rapida de productos.") }
                ]
              },
              {
                element: <RoleGuard roles={["client"]} />,
                children: [
                  { path: "client/dashboard", element: <ClientDashboardPage /> },
                  { path: "client/appointments", element: placeholder("Mis citas", "Tus citas activas e historial.") },
                  { path: "client/book", element: placeholder("Reservar cita", "Wizard de reserva con disponibilidad.") },
                  { path: "client/payments", element: placeholder("Mis pagos", "Historial de pagos propios.") },
                  { path: "client/notifications", element: placeholder("Mis notificaciones", "Notificaciones de citas y pagos.") },
                  { path: "client/profile", element: placeholder("Mi perfil", "Datos personales del cliente.") },
                  { path: "client/penalties", element: placeholder("Mis penalizaciones", "Penalizaciones y reputacion.") }
                ]
              }
            ]
          }
        ]
      },
      {
        path: "*",
        element: <Navigate to="/app/dashboard" replace />
      }
    ]
  }
]);
