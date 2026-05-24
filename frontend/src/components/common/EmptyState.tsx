export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="rounded-lg border bg-card p-6 text-center">
      <p className="font-medium">{title}</p>
      {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
    </div>
  );
}
