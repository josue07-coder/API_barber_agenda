import { api } from "@/lib/api";
import type { DashboardFilters, DashboardOverview } from "@/types/api";

function cleanFilters(filters: DashboardFilters) {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value !== undefined && value !== "")
  );
}

export async function getDashboardOverview(filters: DashboardFilters) {
  const { data } = await api.get<DashboardOverview>("/dashboard/overview", {
    params: cleanFilters(filters)
  });
  return data;
}
