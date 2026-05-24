import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { defaultDateRange } from "@/lib/formatters";
import type { DashboardFilters as DashboardFiltersType } from "@/types/api";

type Props = {
  value: DashboardFiltersType;
  onChange: (value: DashboardFiltersType) => void;
};

export function DashboardFilters({ value, onChange }: Props) {
  return (
    <form
      className="grid gap-3 rounded-lg border bg-card p-4 md:grid-cols-[1fr_1fr_120px]"
      onSubmit={(event) => event.preventDefault()}
    >
      <div className="space-y-2">
        <Label htmlFor="start_date">Desde</Label>
        <Input
          id="start_date"
          type="date"
          value={value.start_date}
          onChange={(event) => onChange({ ...value, start_date: event.target.value })}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="end_date">Hasta</Label>
        <Input
          id="end_date"
          type="date"
          value={value.end_date}
          onChange={(event) => onChange({ ...value, end_date: event.target.value })}
        />
      </div>
      <div className="flex items-end">
        <Button variant="secondary" className="w-full" type="button" onClick={() => onChange(defaultDateRange())}>
          30 dias
        </Button>
      </div>
    </form>
  );
}
