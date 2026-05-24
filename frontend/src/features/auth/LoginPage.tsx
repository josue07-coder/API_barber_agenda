import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiClientError } from "@/lib/api";
import { useAuthStore } from "@/stores/auth.store";

const schema = z.object({
  email: z.string().email("Email invalido"),
  password: z.string().min(1, "La contrasena es requerida")
});

type LoginForm = z.infer<typeof schema>;

function redirectForRole(role: string) {
  return role === "client" ? "/app/client/dashboard" : "/app/dashboard";
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((state) => state.login);
  const user = useAuthStore((state) => state.user);
  const token = useAuthStore((state) => state.token);
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm<LoginForm>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
      password: ""
    }
  });

  if (token && user) {
    return <Navigate to={redirectForRole(user.role)} replace />;
  }

  async function onSubmit(values: LoginForm) {
    setServerError(null);
    try {
      const nextUser = await login(values);
      const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(from ?? redirectForRole(nextUser.role), { replace: true });
    } catch (error) {
      setServerError(error instanceof ApiClientError ? error.message : "No se pudo iniciar sesion");
    }
  }

  return (
    <div className="grid min-h-screen bg-muted/40 px-4 py-8 lg:grid-cols-[1fr_420px]">
      <section className="hidden flex-col justify-between p-10 lg:flex">
        <div>
          <p className="text-sm font-semibold text-primary">BARBER_AGENDA</p>
          <h1 className="mt-6 max-w-2xl text-4xl font-semibold tracking-tight">
            Operacion, agenda y caja para barberias modernas.
          </h1>
          <p className="mt-4 max-w-xl text-muted-foreground">
            Gestiona citas, pagos, sucursales, comisiones e inventario desde un solo panel.
          </p>
        </div>
        <p className="text-sm text-muted-foreground">API local: {import.meta.env.VITE_API_URL}</p>
      </section>
      <section className="flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Iniciar sesion</CardTitle>
            <CardDescription>Usa las credenciales de BARBER_AGENDA.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" autoComplete="email" {...form.register("email")} />
                {form.formState.errors.email ? (
                  <p className="text-xs text-destructive">{form.formState.errors.email.message}</p>
                ) : null}
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Contrasena</Label>
                <Input id="password" type="password" autoComplete="current-password" {...form.register("password")} />
                {form.formState.errors.password ? (
                  <p className="text-xs text-destructive">{form.formState.errors.password.message}</p>
                ) : null}
              </div>
              {serverError ? <p className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{serverError}</p> : null}
              <Button className="w-full" type="submit" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? "Entrando..." : "Entrar"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
