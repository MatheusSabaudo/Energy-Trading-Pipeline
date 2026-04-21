from __future__ import annotations

import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from config import userdata_config as cfg

try:
    from .turin_model import TurinSimulationConfig, generate_hourly_dataset
except ImportError:
    from solar_analysis_data.turin_model import TurinSimulationConfig, generate_hourly_dataset


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "notebooks_output"


def gaussian(hour: int, center: float, width: float) -> float:
    return math.exp(-((hour - center) ** 2) / (2 * width**2))


def build_household_load(rows: list[dict[str, object]], annual_consumption_kwh: float) -> None:
    params = cfg.LOAD_PROFILE_PARAMS
    raw_weights: list[float] = []

    for row in rows:
        timestamp = datetime.fromisoformat(str(row["timestamp"]))
        hour = timestamp.hour
        day_of_year = int(row["day_of_year"])
        weekday = timestamp.weekday()

        morning_peak = params["morning_peak_kw"] * gaussian(hour, 7.5, 1.7)
        evening_peak = params["evening_peak_kw"] * gaussian(hour, 19.5, 2.6)
        midday_bump = 0.16 * gaussian(hour, 13.0, 2.8)
        weekend_bump = params["weekend_bias"] if weekday >= 5 and 10 <= hour <= 16 else 0.0
        winter_factor = 1 + params["winter_bias"] * math.cos((2 * math.pi * (day_of_year - 15)) / 365)
        weight = (
            params["base_load_kw"] + morning_peak + evening_peak + midday_bump + weekend_bump
        ) * winter_factor
        raw_weights.append(weight)

    scale = annual_consumption_kwh / sum(raw_weights)
    for row, weight in zip(rows, raw_weights):
        row["load_kwh"] = round(weight * scale, 6)


def energy_balance(rows: list[dict[str, object]], size_scale: float) -> dict[str, float]:
    annual_production = 0.0
    annual_self_consumed = 0.0
    annual_exported = 0.0
    annual_imported = 0.0
    annual_load = 0.0

    for row in rows:
        production = float(row["hourly_production_kwh"]) * size_scale
        load = float(row["load_kwh"])
        self_consumed = min(production, load)
        exported = max(0.0, production - load)
        imported = max(0.0, load - production)

        annual_production += production
        annual_self_consumed += self_consumed
        annual_exported += exported
        annual_imported += imported
        annual_load += load

    self_consumption_pct = (annual_self_consumed / annual_production * 100) if annual_production else 0.0
    demand_coverage_pct = (annual_self_consumed / annual_load * 100) if annual_load else 0.0
    production_coverage_pct = (annual_production / annual_load * 100) if annual_load else 0.0

    return {
        "annual_production_kwh": annual_production,
        "annual_self_consumed_kwh": annual_self_consumed,
        "annual_exported_kwh": annual_exported,
        "annual_imported_kwh": annual_imported,
        "annual_load_kwh": annual_load,
        "self_consumption_pct": self_consumption_pct,
        "demand_coverage_pct": demand_coverage_pct,
        "production_coverage_pct": production_coverage_pct,
    }


def payback_display(payback_year: int | None) -> str:
    return f"{payback_year} years" if payback_year is not None else "No payback in analysis window"


def evaluate_system_size(
    rows: list[dict[str, object]],
    system_size_kw: float,
    base_system_size_kw: float,
) -> dict[str, object]:
    econ = cfg.ECON_PARAMS
    losses = cfg.LOSS_PARAMS
    size_scale = system_size_kw / base_system_size_kw
    installation_cost = system_size_kw * econ["installation_cost_per_kw"]
    year_one = energy_balance(rows, size_scale)

    cash_flow = [-installation_cost]
    cumulative = [-installation_cost]
    discounted = [-installation_cost]
    yearly_snapshots: list[dict[str, float]] = []
    payback_year = None

    for year in range(1, econ["analysis_years"] + 1):
        degradation = (1 - losses.get("degradation_rate", 0.0)) ** (year - 1)
        balance = energy_balance(rows, size_scale * degradation)
        energy_multiplier = (1 + econ["annual_rate_increase"]) ** (year - 1)
        electricity_rate = econ["electricity_rate"] * energy_multiplier
        sell_back_rate = econ["sell_back_rate"] * energy_multiplier
        incentive_rate = econ["incentive_rate"] * energy_multiplier
        maintenance_cost = econ["annual_maintenance"]

        exchanged_kwh = min(balance["annual_exported_kwh"], balance["annual_imported_kwh"])
        savings = balance["annual_self_consumed_kwh"] * electricity_rate
        export_revenue = balance["annual_exported_kwh"] * sell_back_rate
        incentive = exchanged_kwh * incentive_rate
        yearly_benefit = savings + export_revenue + incentive - maintenance_cost

        if year == losses.get("inverter_replacement_year", econ.get("inverter_replacement_year")):
            yearly_benefit -= losses.get("inverter_replacement_cost", econ.get("inverter_replacement_cost", 0))

        cash_flow.append(yearly_benefit)
        cumulative.append(cumulative[-1] + yearly_benefit)
        discounted.append(yearly_benefit / ((1 + econ["discount_rate"]) ** year))
        yearly_snapshots.append(
            {
                "year": year,
                "annual_production_kwh": balance["annual_production_kwh"],
                "annual_self_consumed_kwh": balance["annual_self_consumed_kwh"],
                "annual_exported_kwh": balance["annual_exported_kwh"],
                "annual_imported_kwh": balance["annual_imported_kwh"],
                "yearly_benefit_euro": yearly_benefit,
            }
        )
        if payback_year is None and cumulative[-1] >= 0:
            payback_year = year

    horizon_20 = min(20, econ["analysis_years"])
    total_benefit_20 = sum(cash_flow[1 : horizon_20 + 1])
    net_profit_20 = cumulative[horizon_20]
    roi_20_years = (net_profit_20 / installation_cost) * 100 if installation_cost else 0.0
    npv_25_years = sum(discounted)

    grid_cost_20_years = 0.0
    for year in range(1, horizon_20 + 1):
        rate = econ["electricity_rate"] * ((1 + econ["annual_rate_increase"]) ** (year - 1))
        grid_cost_20_years += year_one["annual_load_kwh"] * rate

    break_even_rate = (
        max(
            0.0,
            (econ["annual_maintenance"] + installation_cost / 20 - year_one["annual_exported_kwh"] * econ["sell_back_rate"])
            / max(year_one["annual_self_consumed_kwh"], 1e-6),
        )
        if year_one["annual_self_consumed_kwh"] > 0
        else float("inf")
    )

    return {
        "panel_size_kw": system_size_kw,
        "installation_cost_euro": installation_cost,
        "year_one": year_one,
        "cash_flow": cash_flow,
        "cumulative": cumulative,
        "yearly_snapshots": yearly_snapshots,
        "payback_years": payback_year,
        "payback_display": payback_display(payback_year),
        "roi_20_years": roi_20_years,
        "net_profit_20_years_euro": net_profit_20,
        "total_benefit_20_years_euro": total_benefit_20,
        "npv_25_years_euro": npv_25_years,
        "grid_cost_20_years_euro": grid_cost_20_years,
        "net_benefit_vs_grid_20_years_euro": net_profit_20,
        "break_even_rate_euro_per_kwh": break_even_rate,
    }


def build_sensitivity_table(rows: list[dict[str, object]], base_system_size_kw: float) -> list[dict[str, object]]:
    results = []
    for panel_size_kw in [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0]:
        scenario = evaluate_system_size(rows, panel_size_kw, base_system_size_kw)
        year_one = scenario["year_one"]
        results.append(
            {
                "panel_size_kw": panel_size_kw,
                "annual_production_kwh": round(year_one["annual_production_kwh"], 1),
                "self_consumption_pct": round(year_one["self_consumption_pct"], 1),
                "demand_coverage_pct": round(year_one["demand_coverage_pct"], 1),
                "installation_cost_euro": round(scenario["installation_cost_euro"], 0),
                "payback_years": scenario["payback_display"],
                "npv_25_years_euro": round(float(scenario["npv_25_years_euro"]), 0),
            }
        )
    return results


def score_recommendation(scenario: dict[str, object]) -> tuple[int, list[str], list[str]]:
    year_one = scenario["year_one"]
    score = 0
    strengths: list[str] = []
    concerns: list[str] = []
    payback = scenario["payback_years"]
    roi_20 = float(scenario["roi_20_years"])
    demand_coverage = float(year_one["demand_coverage_pct"])
    self_consumption = float(year_one["self_consumption_pct"])

    if payback is not None and payback <= 7:
        score += 35
        strengths.append("Fast payback for a residential PV system")
    elif payback is not None and payback <= 10:
        score += 28
        strengths.append("Healthy payback within a typical asset horizon")
    elif payback is not None and payback <= 13:
        score += 18
        strengths.append("Acceptable payback")
    elif payback is not None and payback <= 16:
        score += 8
        concerns.append("Payback is on the long side")
    else:
        concerns.append("No payback within the analysis window")

    if roi_20 >= 150:
        score += 25
        strengths.append("Strong 20-year ROI")
    elif roi_20 >= 100:
        score += 20
        strengths.append("Solid 20-year ROI")
    elif roi_20 >= 50:
        score += 14
        strengths.append("Positive long-term return")
    elif roi_20 > 0:
        score += 8
        concerns.append("ROI is positive but modest")
    else:
        concerns.append("Negative 20-year ROI")

    if demand_coverage >= 70:
        score += 20
        strengths.append("Covers most of the household demand directly")
    elif demand_coverage >= 55:
        score += 16
        strengths.append("Good direct demand coverage")
    elif demand_coverage >= 40:
        score += 12
        strengths.append("Meaningful reduction in grid purchases")
    elif demand_coverage >= 25:
        score += 6
        concerns.append("Only partial demand coverage")
    else:
        concerns.append("Low direct demand coverage")

    if self_consumption >= 60:
        score += 20
        strengths.append("High self-consumption keeps exported energy limited")
    elif self_consumption >= 45:
        score += 16
        strengths.append("Balanced self-consumption profile")
    elif self_consumption >= 30:
        score += 10
        concerns.append("A notable share of production is exported")
    else:
        concerns.append("Low self-consumption reduces financial efficiency")

    return score, strengths, concerns


def verdict_from_score(score: int) -> str:
    if score >= 80:
        return "HIGHLY RECOMMENDED"
    if score >= 60:
        return "RECOMMENDED"
    if score >= 40:
        return "CONSIDER WITH CAUTION"
    return "NOT RECOMMENDED"


def enrich_rows_for_current_system(rows: list[dict[str, object]], current_system_size_kw: float) -> None:
    base_system_size_kw = float(cfg.PANEL_PARAMS["panel_power_kw"])
    scale = current_system_size_kw / base_system_size_kw
    for row in rows:
        production = float(row["hourly_production_kwh"]) * scale
        load = float(row["load_kwh"])
        row["system_hourly_kwh"] = round(production, 6)
        row["self_consumed_kwh"] = round(min(production, load), 6)
        row["grid_export_kwh"] = round(max(0.0, production - load), 6)
        row["grid_import_kwh"] = round(max(0.0, load - production), 6)


def monthly_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    months: dict[int, dict[str, float]] = {}
    counts: dict[int, int] = {}

    for row in rows:
        month = int(row["month"])
        months.setdefault(
            month,
            {
                "temperature_sum": 0.0,
                "cloud_sum": 0.0,
                "ghi_sum": 0.0,
                "production_sum": 0.0,
                "load_sum": 0.0,
                "self_sum": 0.0,
                "export_sum": 0.0,
                "import_sum": 0.0,
            },
        )
        counts[month] = counts.get(month, 0) + 1
        bucket = months[month]
        bucket["temperature_sum"] += float(row["temperature"])
        bucket["cloud_sum"] += float(row["cloudcover"])
        bucket["ghi_sum"] += float(row["ghi_wm2"])
        bucket["production_sum"] += float(row["system_hourly_kwh"])
        bucket["load_sum"] += float(row["load_kwh"])
        bucket["self_sum"] += float(row["self_consumed_kwh"])
        bucket["export_sum"] += float(row["grid_export_kwh"])
        bucket["import_sum"] += float(row["grid_import_kwh"])

    summary: list[dict[str, object]] = []
    for month in range(1, 13):
        bucket = months[month]
        count = counts[month]
        summary.append(
            {
                "month": month,
                "avg_temperature_c": round(bucket["temperature_sum"] / count, 2),
                "avg_cloud_cover_pct": round(bucket["cloud_sum"] / count, 1),
                "avg_ghi_wm2": round(bucket["ghi_sum"] / count, 1),
                "production_kwh": round(bucket["production_sum"], 1),
                "load_kwh": round(bucket["load_sum"], 1),
                "self_consumed_kwh": round(bucket["self_sum"], 1),
                "grid_export_kwh": round(bucket["export_sum"], 1),
                "grid_import_kwh": round(bucket["import_sum"], 1),
            }
        )
    return summary


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_text_report(
    current: dict[str, object],
    optimal: dict[str, object],
    score: int,
    verdict: str,
    strengths: list[str],
    concerns: list[str],
    monthly: list[dict[str, object]],
    year: int,
) -> str:
    current_year_one = current["year_one"]
    optimal_year_one = optimal["year_one"]
    best_month = max(monthly, key=lambda row: float(row["production_kwh"]))
    worst_month = min(monthly, key=lambda row: float(row["production_kwh"]))

    lines = [
        "=" * 68,
        "TURIN SOLAR PV ANALYSIS - RELIABLE SIMULATION",
        "=" * 68,
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Simulation year: {year}",
        f"Location: {cfg.LOCATION_PARAMS['city']}, {cfg.LOCATION_PARAMS['country']}",
        "",
        f"VERDICT: {verdict}",
        f"Score: {score}/100",
        "",
        "CURRENT SYSTEM",
        f"  Size: {current['panel_size_kw']} kWp",
        f"  Annual production: {float(current_year_one['annual_production_kwh']):.0f} kWh",
        f"  Self-consumption: {float(current_year_one['self_consumption_pct']):.1f}%",
        f"  Demand coverage: {float(current_year_one['demand_coverage_pct']):.1f}%",
        f"  Payback: {current['payback_display']}",
        f"  20-year net profit: EUR {float(current['net_profit_20_years_euro']):,.0f}",
        f"  25-year NPV: EUR {float(current['npv_25_years_euro']):,.0f}",
        "",
        "BEST SIZE TESTED",
        f"  Size: {optimal['panel_size_kw']} kWp",
        f"  Annual production: {float(optimal_year_one['annual_production_kwh']):.0f} kWh",
        f"  Self-consumption: {float(optimal_year_one['self_consumption_pct']):.1f}%",
        f"  Demand coverage: {float(optimal_year_one['demand_coverage_pct']):.1f}%",
        f"  Payback: {optimal['payback_display']}",
        f"  20-year net profit: EUR {float(optimal['net_profit_20_years_euro']):,.0f}",
        f"  25-year NPV: EUR {float(optimal['npv_25_years_euro']):,.0f}",
        "",
        "SEASONAL HIGHLIGHTS",
        f"  Best production month: {best_month['month']:02d} with {best_month['production_kwh']} kWh",
        f"  Weakest production month: {worst_month['month']:02d} with {worst_month['production_kwh']} kWh",
        "",
        "STRENGTHS",
    ]

    if strengths:
        lines.extend(f"  - {item}" for item in strengths)
    else:
        lines.append("  - None strong enough to offset the economic concerns")

    lines.append("")
    lines.append("CONCERNS")
    if concerns:
        lines.extend(f"  - {item}" for item in concerns)
    else:
        lines.append("  - No major red flags in the modeled scenario")

    lines.extend(
        [
            "",
            "NOTES",
            "  - Weather is simulated hour by hour from Turin climate normals plus deterministic daily variation.",
            "  - Solar production uses sun position, clear-sky irradiance, cloud attenuation, tilt/orientation, and temperature derating.",
            "  - Financials use hourly self-consumption against a normalized residential load profile, not a fixed percentage guess.",
            "",
        ]
    )

    return "\n".join(lines)


def run_reliable_analysis(year: int | None = None) -> dict[str, object]:
    year = year or cfg.SIMULATION_PARAMS["analysis_year"]
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    config = TurinSimulationConfig(system_size_kw=cfg.PANEL_PARAMS["panel_power_kw"])
    rows = generate_hourly_dataset(year, config=config)
    build_household_load(rows, cfg.ECON_PARAMS["household_consumption"])

    current = evaluate_system_size(rows, cfg.PANEL_PARAMS["panel_power_kw"], config.system_size_kw)
    sensitivity = build_sensitivity_table(rows, config.system_size_kw)

    candidate_sizes = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0]
    scenarios = [evaluate_system_size(rows, size, config.system_size_kw) for size in candidate_sizes]
    optimal = max(
        scenarios,
        key=lambda scenario: (
            float(scenario["npv_25_years_euro"]),
            -999 if scenario["payback_years"] is None else -int(scenario["payback_years"]),
            -float(scenario["panel_size_kw"]),
        ),
    )

    score, strengths, concerns = score_recommendation(optimal)
    verdict = verdict_from_score(score)

    enrich_rows_for_current_system(rows, float(current["panel_size_kw"]))
    monthly = monthly_summary(rows)

    dataset_path = DATA_DIR / f"turin_hourly_simulated_{year}.csv"
    monthly_path = OUTPUT_DIR / "reliable_monthly_summary.csv"
    summary_path = OUTPUT_DIR / "reliable_analysis_summary.json"
    report_path = OUTPUT_DIR / "reliable_final_recommendations.txt"

    write_csv(dataset_path, rows, list(rows[0].keys()))
    write_csv(monthly_path, monthly, list(monthly[0].keys()))

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "simulation_year": year,
        "location": cfg.LOCATION_PARAMS,
        "current_system": current,
        "optimal_system": optimal,
        "sensitivity": sensitivity,
        "monthly_summary": monthly,
        "score": score,
        "verdict": verdict,
        "strengths": strengths,
        "concerns": concerns,
        "dataset_path": str(dataset_path.relative_to(ROOT_DIR)),
    }

    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    report_text = build_text_report(current, optimal, score, verdict, strengths, concerns, monthly, year)
    report_path.write_text(report_text, encoding="utf-8")

    return {
        "dataset_path": dataset_path,
        "monthly_path": monthly_path,
        "summary_path": summary_path,
        "report_path": report_path,
        "summary": summary,
    }


def main() -> None:
    result = run_reliable_analysis()
    print(f"Dataset written to: {result['dataset_path']}")
    print(f"Monthly summary written to: {result['monthly_path']}")
    print(f"Summary JSON written to: {result['summary_path']}")
    print(f"Report written to: {result['report_path']}")
    print(f"Verdict: {result['summary']['verdict']}")


if __name__ == "__main__":
    main()
