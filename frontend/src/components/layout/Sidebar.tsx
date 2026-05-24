import {
  BarChart3,
  Bell,
  BriefcaseBusiness,
  CalendarDays,
  ClipboardList,
  CreditCard,
  DollarSign,
  Home,
  Landmark,
  MapPin,
  Package,
  Scissors,
  UserRound,
  Users
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import type { Role } from "@/types/api";

const navByRole: Record<Role, Array<{ label: string; to: string; icon: React.ElementType }>> = {
  admin: [
    { label: "Dashboard", to: "/app/dashboard", icon: Home },
    { label: "Agenda", to: "/app/calendar", icon: CalendarDays },
    { label: "Clientes", to: "/app/clients", icon: Users },
    { label: "Barberos", to: "/app/barbers", icon: Scissors },
    { label: "Servicios", to: "/app/services", icon: BriefcaseBusiness },
    { label: "Sucursales", to: "/app/branches", icon: MapPin },
    { label: "Pagos", to: "/app/payments", icon: CreditCard },
    { label: "Caja", to: "/app/cash", icon: Landmark },
    { label: "Comisiones", to: "/app/commissions", icon: DollarSign },
    { label: "Inventario", to: "/app/inventory", icon: Package },
    { label: "Reportes", to: "/app/reports", icon: BarChart3 },
    { label: "Notificaciones", to: "/app/notifications", icon: Bell }
  ],
  barber: [
    { label: "Dashboard", to: "/app/dashboard", icon: Home },
    { label: "Agenda", to: "/app/calendar", icon: CalendarDays },
    { label: "Clientes", to: "/app/clients", icon: Users },
    { label: "Pagos", to: "/app/payments", icon: CreditCard },
    { label: "Caja", to: "/app/cash", icon: Landmark },
    { label: "Comisiones", to: "/app/my-commissions", icon: DollarSign },
    { label: "POS", to: "/app/pos", icon: Package },
    { label: "Notificaciones", to: "/app/notifications", icon: Bell }
  ],
  client: [
    { label: "Inicio", to: "/app/client/dashboard", icon: Home },
    { label: "Mis citas", to: "/app/client/appointments", icon: ClipboardList },
    { label: "Reservar", to: "/app/client/book", icon: CalendarDays },
    { label: "Pagos", to: "/app/client/payments", icon: CreditCard },
    { label: "Perfil", to: "/app/client/profile", icon: UserRound },
    { label: "Notificaciones", to: "/app/client/notifications", icon: Bell }
  ]
};

export function Sidebar({ role }: { role: Role }) {
  const items = navByRole[role];

  return (
    <aside className="hidden w-64 shrink-0 border-r bg-card md:block">
      <div className="flex h-16 items-center border-b px-5">
        <div>
          <p className="font-semibold">BARBER_AGENDA</p>
          <p className="text-xs text-muted-foreground">Panel {role}</p>
        </div>
      </div>
      <nav className="space-y-1 p-3">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                  isActive && "bg-muted text-foreground"
                )
              }
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
