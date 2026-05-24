import { Link } from "react-router-dom";

export function ForbiddenPage() {
  return (
    <div className="grid min-h-screen place-items-center bg-muted/40 p-6">
      <div className="max-w-md text-center">
        <h1 className="text-2xl font-semibold">Acceso denegado</h1>
        <p className="mt-2 text-sm text-muted-foreground">Tu rol no tiene permisos para ver esta seccion.</p>
        <Link
          to="/app/dashboard"
          className="mt-5 inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Volver al panel
        </Link>
      </div>
    </div>
  );
}
