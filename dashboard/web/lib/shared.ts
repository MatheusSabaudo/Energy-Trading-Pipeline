export type YearOneMetrics = {
  annual_production_kwh: number;
  annual_self_consumed_kwh: number;
  annual_exported_kwh: number;
  annual_imported_kwh: number;
  annual_load_kwh: number;
  self_consumption_pct: number;
  demand_coverage_pct: number;
  production_coverage_pct: number;
};

export type ScenarioMetrics = {
  panel_size_kw: number;
  installation_cost_euro: number;
  year_one: YearOneMetrics;
  cash_flow: number[];
  cumulative: number[];
  payback_years: number | null;
  payback_display: string;
  roi_20_years: number;
  net_profit_20_years_euro: number;
  total_benefit_20_years_euro: number;
  npv_25_years_euro: number;
  grid_cost_20_years_euro: number;
  net_benefit_vs_grid_20_years_euro: number;
  break_even_rate_euro_per_kwh: number;
};

export type MonthlySummary = {
  month: number;
  avg_temperature_c: number;
  avg_cloud_cover_pct: number;
  avg_ghi_wm2: number;
  production_kwh: number;
  load_kwh: number;
  self_consumed_kwh: number;
  grid_export_kwh: number;
  grid_import_kwh: number;
};

export type SensitivityRow = {
  panel_size_kw: number;
  annual_production_kwh: number;
  self_consumption_pct: number;
  demand_coverage_pct: number;
  installation_cost_euro: number;
  payback_years: string;
  npv_25_years_euro: number;
};

export function formatCompactNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: value >= 1000 ? 1 : 0
  }).format(value);
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-IT", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0
  }).format(value);
}

export function formatDecimal(value: number, digits = 1): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  }).format(value);
}

export function monthLabel(month: number): string {
  return new Date(2026, month - 1, 1).toLocaleString("en-US", { month: "short" });
}
