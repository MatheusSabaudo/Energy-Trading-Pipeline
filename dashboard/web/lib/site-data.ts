import fs from "node:fs";
import path from "node:path";
import type { MonthlySummary, ScenarioMetrics, SensitivityRow, YearOneMetrics } from "./shared";
export {
  formatCompactNumber,
  formatCurrency,
  formatDecimal,
  monthLabel,
  type MonthlySummary,
  type ScenarioMetrics,
  type SensitivityRow,
  type YearOneMetrics
} from "./shared";

export type AnalysisSummary = {
  generated_at: string;
  simulation_year: number;
  location: {
    city: string;
    country: string;
    latitude: number;
    longitude: number;
    timezone: string;
    elevation_m: number;
  };
  current_system: ScenarioMetrics;
  optimal_system: ScenarioMetrics;
  sensitivity: SensitivityRow[];
  monthly_summary: MonthlySummary[];
  score: number;
  verdict: string;
  strengths: string[];
  concerns: string[];
  dataset_path: string;
};

export type PipelineStage = {
  title: string;
  summary: string;
  details: string[];
  accent: string;
};

export function getAnalysisSummary(): AnalysisSummary {
  const summaryPath = path.join(
    process.cwd(),
    "..",
    "..",
    "solar_analysis_data",
    "notebooks_output",
    "reliable_analysis_summary.json"
  );

  const raw = fs.readFileSync(summaryPath, "utf-8");
  return JSON.parse(raw) as AnalysisSummary;
}

export function getPipelineStages(): PipelineStage[] {
  return [
    {
      title: "Ingestion",
      summary: "Two sources enter the platform: WeatherStack API payloads and simulated IoT panel events from Kafka.",
      details: [
        "Weather fetcher lands ambient measurements into bronze weather tables.",
        "Turin-aware solar producer emits realistic production, temperature, and cloud factors.",
        "Kafka acts as the streaming boundary before persistence."
      ],
      accent: "sun"
    },
    {
      title: "Storage",
      summary: "PostgreSQL is the operational backbone for bronze, silver, and gold layers.",
      details: [
        "Bronze stores raw events with minimal transformation.",
        "Silver adds validation, quality flags, categories, and derived operational metrics.",
        "Gold delivers KPI-ready aggregates for panel performance and anomaly tracking."
      ],
      accent: "sea"
    },
    {
      title: "Transformation",
      summary: "Airflow DAGs orchestrate the medallion progression and anomaly workflows.",
      details: [
        "Ingestion DAG refreshes source data on a schedule.",
        "Silver and gold DAGs reshape the data into analytical tables.",
        "Monitoring DAGs track freshness, health, and unusual behavior."
      ],
      accent: "sand"
    },
    {
      title: "Serving",
      summary: "Business intelligence, feasibility analysis, and portfolio storytelling sit on top of the curated data.",
      details: [
        "The reliable Turin simulation produces year-scale economics and seasonality outputs.",
        "This website packages both the technical architecture and the decision-facing insights.",
        "Outputs are deployable as a Vercel-hosted experience for demos and portfolio reviews."
      ],
      accent: "ember"
    }
  ];
}

export function getDagSteps(): string[] {
  return [
    "01 ingestion pipeline",
    "02 silver transform",
    "03 gold load",
    "04 anomaly detection",
    "05 pipeline monitor"
  ];
}

export function getStackItems(): string[] {
  return [
    "Python",
    "PostgreSQL",
    "Apache Kafka",
    "Apache Airflow",
    "Docker Compose",
    "WeatherStack API",
    "Next.js on Vercel"
  ];
}

export function getDataProducts(): string[] {
  return [
    "bronze weather_data",
    "bronze solar_panel_readings",
    "silver_weather",
    "silver_solar",
    "gold_daily_panel",
    "gold_hourly_system",
    "gold_monthly_kpis",
    "gold_anomalies"
  ];
}
