export function LoadingState({ label = "Cargando..." }: { label?: string }) {
  return (
    <div className="flex min-h-48 items-center justify-center rounded-lg border bg-card text-sm text-muted-foreground">
      {label}
    </div>
  );
}
