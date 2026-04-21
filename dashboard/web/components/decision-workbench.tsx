"use client";

import { useMemo, useState } from "react";
import {
  formatCurrency,
  formatDecimal,
  type ScenarioMetrics,
  type SensitivityRow
} from "../lib/shared";

type ClientProfile = "homeowner" | "small_business" | "big_business";
type Priority = "payback" | "value" | "coverage";
type BudgetBand = "lean" | "balanced" | "premium";
type Horizon = "short" | "medium" | "long";

type DecisionWorkbenchProps = {
  current: ScenarioMetrics;
  optimal: ScenarioMetrics;
  sensitivity: SensitivityRow[];
};

type RankedScenario = SensitivityRow & {
  rankingScore: number;
  scoreBreakdown: {
    payback: number;
    value: number;
    coverage: number;
    selfConsumption: number;
    capex: number;
    production: number;
  };
  withinBudget: boolean;
};

const profileCopy: Record<
  ClientProfile,
  {
    title: string;
    range: string;
    summary: string;
    actions: string[];
  }
> = {
  homeowner: {
    title: "Home owner",
    range: "8-12 panels • lighter investment",
    summary: "Best for residential-size systems where panel count and upfront spend need to stay easy to justify.",
    actions: [
      "Lead with total panel count, initial investment, and yearly bill reduction.",
      "Use the ranked scenarios to show when extra panels stop improving the economics enough.",
      "Keep the recommendation anchored on an investment that feels realistic for a household."
    ]
  },
  small_business: {
    title: "Small business",
    range: "12-16 panels • balanced investment",
    summary: "Best for small commercial sites that can support a mid-range panel count and want a balanced capex profile.",
    actions: [
      "Frame the discussion around installed panels, investment required, and operating savings.",
      "Use the ranking to show when a mid-sized system creates stronger lifetime value.",
      "Treat surplus energy as a trade-off that can be managed, not an automatic drawback."
    ]
  },
  big_business: {
    title: "Big business",
    range: "16-20 panels • strategic investment",
    summary: "Best for larger sites that can absorb a bigger solar footprint and evaluate the decision as a strategic investment.",
    actions: [
      "Lead with installed scale, capex commitment, and long-run portfolio value.",
      "Use the ranking to compare how larger panel counts shift coverage and NPV.",
      "Position the recommendation as an investment strategy, not only a savings story."
    ]
  }
};

const KW_PER_PANEL = 0.3;

function panelCountFromKw(panelSizeKw: number): number {
  return Math.max(1, Math.round(panelSizeKw / KW_PER_PANEL));
}

function budgetLimit(budget: BudgetBand): number {
  if (budget === "lean") {
    return 4500;
  }
  if (budget === "balanced") {
    return 7200;
  }
  return Number.POSITIVE_INFINITY;
}

function budgetLabel(budget: BudgetBand): string {
  if (budget === "lean") {
    return "Up to €4.5k";
  }
  if (budget === "balanced") {
    return "Up to €7.2k";
  }
  return "Full sizing range";
}

function numericPayback(payback: string): number {
  const parsed = Number.parseFloat(payback);
  return Number.isFinite(parsed) ? parsed : 99;
}

function normalize(value: number, min: number, max: number): number {
  if (max === min) {
    return 0.5;
  }
  return (value - min) / (max - min);
}

function computeWeights(profile: ClientProfile, priority: Priority, horizon: Horizon) {
  const weights = {
    payback: 0.22,
    value: 0.2,
    coverage: 0.18,
    selfConsumption: 0.14,
    capex: 0.14,
    production: 0.12
  };

  if (profile === "homeowner") {
    weights.payback += 0.1;
    weights.capex += 0.1;
    weights.selfConsumption += 0.04;
    weights.value -= 0.08;
    weights.production -= 0.05;
  }

  if (profile === "small_business") {
    weights.value += 0.08;
    weights.coverage += 0.06;
    weights.production += 0.04;
    weights.capex -= 0.03;
    weights.selfConsumption -= 0.02;
  }

  if (profile === "big_business") {
    weights.value += 0.14;
    weights.coverage += 0.1;
    weights.production += 0.08;
    weights.capex -= 0.08;
    weights.selfConsumption -= 0.04;
  }

  if (priority === "payback") {
    weights.payback += 0.28;
    weights.capex += 0.12;
    weights.value -= 0.1;
    weights.production -= 0.04;
  }

  if (priority === "value") {
    weights.value += 0.3;
    weights.production += 0.08;
    weights.capex -= 0.08;
    weights.payback -= 0.06;
  }

  if (priority === "coverage") {
    weights.coverage += 0.28;
    weights.production += 0.1;
    weights.selfConsumption += 0.04;
    weights.capex -= 0.06;
  }

  if (horizon === "short") {
    weights.payback += 0.18;
    weights.capex += 0.12;
    weights.value -= 0.12;
    weights.production -= 0.05;
  }

  if (horizon === "long") {
    weights.value += 0.16;
    weights.coverage += 0.08;
    weights.production += 0.08;
    weights.capex -= 0.08;
    weights.payback -= 0.08;
  }

  const total = Object.values(weights).reduce((sum, value) => sum + value, 0);
  return {
    payback: weights.payback / total,
    value: weights.value / total,
    coverage: weights.coverage / total,
    selfConsumption: weights.selfConsumption / total,
    capex: weights.capex / total,
    production: weights.production / total
  };
}

function rankScenarios({
  sensitivity,
  profile,
  priority,
  budget,
  horizon,
  current
}: {
  sensitivity: SensitivityRow[];
  profile: ClientProfile;
  priority: Priority;
  budget: BudgetBand;
  horizon: Horizon;
  current: ScenarioMetrics;
}): RankedScenario[] {
  const weights = computeWeights(profile, priority, horizon);
  const budgetCap = budgetLimit(budget);

  const paybacks = sensitivity.map((row) => numericPayback(row.payback_years));
  const npvs = sensitivity.map((row) => row.npv_25_years_euro);
  const coverages = sensitivity.map((row) => row.demand_coverage_pct);
  const selfConsumptions = sensitivity.map((row) => row.self_consumption_pct);
  const capexes = sensitivity.map((row) => row.installation_cost_euro);
  const productions = sensitivity.map((row) => row.annual_production_kwh);

  const minPayback = Math.min(...paybacks);
  const maxPayback = Math.max(...paybacks);
  const minNpv = Math.min(...npvs);
  const maxNpv = Math.max(...npvs);
  const minCoverage = Math.min(...coverages);
  const maxCoverage = Math.max(...coverages);
  const minSelf = Math.min(...selfConsumptions);
  const maxSelf = Math.max(...selfConsumptions);
  const minCapex = Math.min(...capexes);
  const maxCapex = Math.max(...capexes);
  const minProduction = Math.min(...productions);
  const maxProduction = Math.max(...productions);

  return sensitivity
    .map((row) => {
      const withinBudget = row.installation_cost_euro <= budgetCap;
      const paybackScore = 1 - normalize(numericPayback(row.payback_years), minPayback, maxPayback);
      const valueScore = normalize(row.npv_25_years_euro, minNpv, maxNpv);
      const coverageScore = normalize(row.demand_coverage_pct, minCoverage, maxCoverage);
      const selfConsumptionScore = normalize(row.self_consumption_pct, minSelf, maxSelf);
      const capexScore = 1 - normalize(row.installation_cost_euro, minCapex, maxCapex);
      const productionScore = normalize(row.annual_production_kwh, minProduction, maxProduction);

      let rankingScore =
        paybackScore * weights.payback +
        valueScore * weights.value +
        coverageScore * weights.coverage +
        selfConsumptionScore * weights.selfConsumption +
        capexScore * weights.capex +
        productionScore * weights.production;

      if (!withinBudget) {
        rankingScore -= budget === "premium" ? 0 : 0.45;
      }

      if (budget === "lean" && row.panel_size_kw > current.panel_size_kw) {
        rankingScore -= 0.08;
      }

      if (profile === "homeowner" && row.self_consumption_pct < 25) {
        rankingScore -= 0.08;
      }

      if (profile === "homeowner" && row.panel_size_kw > 3.5) {
        rankingScore -= 0.1;
      }

      if (profile === "small_business" && row.panel_size_kw >= 3 && row.panel_size_kw <= 4.5) {
        rankingScore += 0.05;
      }

      if (profile === "big_business" && row.panel_size_kw >= 4.5) {
        rankingScore += 0.08;
      }

      if (priority === "coverage" && row.demand_coverage_pct > current.year_one.demand_coverage_pct) {
        rankingScore += 0.04;
      }

      if (priority === "payback" && row.installation_cost_euro < current.installation_cost_euro) {
        rankingScore += 0.03;
      }

      return {
        ...row,
        withinBudget,
        rankingScore,
        scoreBreakdown: {
          payback: paybackScore,
          value: valueScore,
          coverage: coverageScore,
          selfConsumption: selfConsumptionScore,
          capex: capexScore,
          production: productionScore
        }
      };
    })
    .sort((a, b) => b.rankingScore - a.rankingScore);
}

function decisionNarrative({
  profile,
  priority,
  selected,
  current
}: {
  profile: ClientProfile;
  priority: Priority;
  selected: RankedScenario;
  current: ScenarioMetrics;
}) {
  const movedUp = selected.panel_size_kw > current.panel_size_kw;
  const movedDown = selected.panel_size_kw < current.panel_size_kw;

  if (priority === "payback") {
    return {
      headline: `${profileCopy[profile].title}: prioritize speed to financial return`,
      body: movedDown
        ? `The workbench prefers a smaller panel count because investment discipline and payback speed dominate the current settings.`
        : movedUp
          ? `The workbench still accepts a larger panel count because its economics remain strong even under a stricter payback lens.`
          : `The current system remains the cleanest answer when the conversation is centered on fast, defendable payback.`,
      actionLabel: "Lead the conversation with panel count, investment, and near-term confidence."
    };
  }

  if (priority === "value") {
    return {
      headline: `${profileCopy[profile].title}: maximize long-run financial value`,
      body: movedUp
        ? `The recommendation moves upward because long-term value now justifies a higher panel count and a bigger upfront investment.`
        : `The recommendation stays disciplined because this configuration creates the best value within the selected investment band and horizon.`,
      actionLabel: "Explain why lifetime value can justify more panels and a larger capex envelope."
    };
  }

  return {
    headline: `${profileCopy[profile].title}: increase operational energy coverage`,
    body: movedUp
      ? `The recommendation shifts to a larger panel count because the selected decision mode favors stronger on-site coverage and lower grid dependence.`
      : `The recommendation stays close to the baseline because extra panels improve coverage only marginally beyond this point under the selected constraints.`,
    actionLabel: "Frame the recommendation around panel count, imports avoided, and operational visibility."
  };
}

function topReasons(selected: RankedScenario, current: ScenarioMetrics) {
  const reasons = [];

  if (selected.panel_size_kw > current.panel_size_kw) {
    reasons.push("A larger panel count improves strategic upside in the selected decision mode.");
  } else if (selected.panel_size_kw < current.panel_size_kw) {
    reasons.push("A smaller panel count keeps the investment lower without collapsing recommendation quality.");
  } else {
    reasons.push("The baseline panel count remains the most balanced option under the current settings.");
  }

  if (selected.withinBudget) {
    reasons.push("The recommended investment stays inside the selected budget band.");
  } else {
    reasons.push("No candidate fully fits the budget band, so the strongest available investment fallback is shown.");
  }

  if (selected.self_consumption_pct >= 30) {
    reasons.push("Self-consumption remains high enough to keep the exported-energy story manageable.");
  } else {
    reasons.push("Lower self-consumption is accepted because the chosen priority favors another dimension more strongly.");
  }

  return reasons;
}

function recommendationTone(priority: Priority): {
  eyebrow: string;
  title: string;
  summary: string;
} {
  if (priority === "payback") {
    return {
      eyebrow: "Fast-return mode",
      title: "Optimize for lower risk and faster financial clarity",
      summary: "This mode prioritizes lighter capex pressure, better payback speed, and easier commercial approval."
    };
  }

  if (priority === "value") {
    return {
      eyebrow: "Value mode",
      title: "Optimize for stronger lifetime economics",
      summary: "This mode rewards configurations that build more value over time, even when they require a bigger upfront investment."
    };
  }

  return {
    eyebrow: "Coverage mode",
    title: "Optimize for reduced grid dependence",
    summary: "This mode favors options that push more energy coverage on-site and make the solar-vs-grid advantage more visible."
  };
}

export default function DecisionWorkbench({
  current,
  optimal,
  sensitivity
}: DecisionWorkbenchProps) {
  const [profile, setProfile] = useState<ClientProfile>("homeowner");
  const [priority, setPriority] = useState<Priority>("payback");
  const [budget, setBudget] = useState<BudgetBand>("balanced");
  const [horizon, setHorizon] = useState<Horizon>("medium");

  const ranked = useMemo(
    () => rankScenarios({ sensitivity, profile, priority, budget, horizon, current }),
    [sensitivity, profile, priority, budget, horizon, current]
  );

  const selected = ranked[0];
  const topOptions = ranked.slice(0, 4);
  const excludedCount = ranked.filter((row) => !row.withinBudget).length;
  const narrative = useMemo(
    () => decisionNarrative({ profile, priority, selected, current }),
    [profile, priority, selected, current]
  );
  const reasons = useMemo(() => topReasons(selected, current), [selected, current]);
  const tone = useMemo(() => recommendationTone(priority), [priority]);

  const currentGridCost20 = current.grid_cost_20_years_euro;
  const selectedNetBenefit20 = selected.npv_25_years_euro;
  const currentSolarVsGridDelta = current.net_benefit_vs_grid_20_years_euro;

  return (
    <section className="workbench">
      <div className="workbench-result">
        <div className="result-top">
          <div>
            <span className="eyebrow">{tone.eyebrow}</span>
            <h3>{narrative.headline}</h3>
            <p>{narrative.body}</p>
          </div>
          <div className="recommendation-badge priority">
            <span>Recommended scenario</span>
            <strong>{formatDecimal(selected.panel_size_kw, 1)} kWp</strong>
            <p>{tone.title}</p>
          </div>
        </div>

        <div className="recommendation-banner">
          <div>
            <span>{tone.eyebrow}</span>
            <strong>{tone.title}</strong>
          </div>
          <p>{tone.summary}</p>
        </div>
        <div className="recommendation-strip">
          <div>
            <span>Estimated panels</span>
            <strong>{panelCountFromKw(selected.panel_size_kw)}</strong>
          </div>
          <div>
            <span>Estimated investment</span>
            <strong>{formatCurrency(selected.installation_cost_euro)}</strong>
          </div>
          <div>
            <span>Budget filter</span>
            <strong>{budgetLabel(budget)}</strong>
          </div>
          <div>
            <span>Payback</span>
            <strong>{selected.payback_years}</strong>
          </div>
        </div>

        <div className="comparison-band">
          <article className="comparison-stat grid">
            <span>Traditional grid cost over 20 years</span>
            <strong>{formatCurrency(currentGridCost20)}</strong>
            <p>Modeled cost of staying fully dependent on the traditional energy system.</p>
          </article>
          <article className="comparison-stat solar">
            <span>Selected scenario value signal</span>
            <strong>{formatCurrency(selectedNetBenefit20)}</strong>
            <p>Long-run value indicator for the selected solar setup under the active decision settings.</p>
          </article>
          <article className="comparison-stat delta">
            <span>Current solar vs grid delta</span>
            <strong>{formatCurrency(currentSolarVsGridDelta)}</strong>
            <p>Direct comparison between the modeled current solar baseline and the traditional grid-only path.</p>
          </article>
        </div>

        <div className="decision-grid">
          <article className="decision-card">
            <span className="eyebrow">What to emphasize</span>
            <h4>{narrative.actionLabel}</h4>
            <ul>
              {profileCopy[profile].actions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>

          <article className="decision-card comparison">
            <span className="eyebrow">Why this option wins</span>
            <div className="decision-stats">
              <div>
                <span>Current size</span>
                <strong>{formatDecimal(current.panel_size_kw, 1)} kWp</strong>
              </div>
              <div>
                <span>Suggested size</span>
                <strong>{formatDecimal(selected.panel_size_kw, 1)} kWp</strong>
              </div>
              <div>
                <span>Current panels</span>
                <strong>{panelCountFromKw(current.panel_size_kw)}</strong>
              </div>
              <div>
                <span>Suggested panels</span>
                <strong>{panelCountFromKw(selected.panel_size_kw)}</strong>
              </div>
              <div>
                <span>Suggested investment</span>
                <strong>{formatCurrency(selected.installation_cost_euro)}</strong>
              </div>
              <div>
                <span>Ranking score</span>
                <strong>{formatDecimal(selected.rankingScore * 100, 0)}</strong>
              </div>
            </div>
            <ul className="compact-list">
              {reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </article>
        </div>
      </div>

      <div className="simulation-lab">
        <div className="simulation-head">
          <div>
            <span className="eyebrow">Simulation quadrant</span>
            <h3>Change the decision drivers without disturbing the executive surface</h3>
            <p>
              This lower workspace isolates the interactive controls and scenario reshuffling, so the top recommendation
              area keeps the same structure while you explain trade-offs live.
            </p>
          </div>
          <div className="lab-benchmark">
            <span>Best tested benchmark</span>
            <strong>{formatDecimal(optimal.panel_size_kw, 1)} kWp</strong>
            <p>{formatCurrency(optimal.npv_25_years_euro)} 25-year NPV</p>
          </div>
        </div>

        <div className="simulation-quadrant">
          <div className="workbench-controls">
            <div className="workbench-head">
              <span className="eyebrow">Interaction panel</span>
              <h3>Adjust the scenario inputs and watch the ranking update below</h3>
              <p>
                The recommendation reacts to the selected client profile, strategic priority, budget guardrail, and
                ownership horizon. This area works like a focused simulation lab instead of changing the whole section
                layout.
              </p>
            </div>

            <div className="control-group">
              <span className="control-label">Client profile</span>
              <div className="segmented-grid">
                {(["homeowner", "small_business", "big_business"] as ClientProfile[]).map((item) => (
                  <button
                    key={item}
                    type="button"
                    className={`segment-button ${profile === item ? "active" : ""}`}
                    onClick={() => setProfile(item)}
                  >
                    <strong>{profileCopy[item].title}</strong>
                    <span>{profileCopy[item].range}</span>
                    <small>{profileCopy[item].summary}</small>
                  </button>
                ))}
              </div>
            </div>

            <div className="control-group">
              <span className="control-label">Decision priority</span>
              <div className="chip-row">
                {[
                  { key: "payback", label: "Fast payback" },
                  { key: "value", label: "Highest value" },
                  { key: "coverage", label: "More energy coverage" }
                ].map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    className={`choice-chip ${priority === item.key ? "active" : ""}`}
                    onClick={() => setPriority(item.key as Priority)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="control-grid">
              <div className="control-group">
                <span className="control-label">Budget band</span>
                <div className="chip-row vertical">
                  {[
                    { key: "lean", label: "Lean" },
                    { key: "balanced", label: "Balanced" },
                    { key: "premium", label: "Premium" }
                  ].map((item) => (
                    <button
                      key={item.key}
                      type="button"
                      className={`choice-chip ${budget === item.key ? "active" : ""}`}
                      onClick={() => setBudget(item.key as BudgetBand)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="control-group">
                <span className="control-label">Ownership horizon</span>
                <div className="chip-row vertical">
                  {[
                    { key: "short", label: "Short term" },
                    { key: "medium", label: "Medium term" },
                    { key: "long", label: "Long term" }
                  ].map((item) => (
                    <button
                      key={item.key}
                      type="button"
                      className={`choice-chip ${horizon === item.key ? "active" : ""}`}
                      onClick={() => setHorizon(item.key as Horizon)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <aside className="ranking-section">
            <div className="ranking-head">
              <div>
                <span className="eyebrow">Scenario ranking</span>
                <h4>How the top options reorder under the current decision settings</h4>
              </div>
              <p>
                {excludedCount > 0
                  ? `${excludedCount} scenario${excludedCount > 1 ? "s are" : " is"} outside the current budget band.`
                  : "All scenarios fit inside the selected budget band."}
              </p>
            </div>

            <div className="ranking-grid">
              {topOptions.map((row, index) => (
                <article
                  key={`${row.panel_size_kw}-${index}`}
                  className={`ranking-card ${index === 0 ? "winner" : ""} ${!row.withinBudget ? "muted" : ""}`}
                >
                  <div className="ranking-top">
                    <span className="rank-index">#{index + 1}</span>
                    <strong>{formatDecimal(row.panel_size_kw, 1)} kWp</strong>
                  </div>
                  <p>{row.withinBudget ? "Within budget" : "Outside budget"}</p>
                  <div className="ranking-metrics">
                  <div>
                    <span>Panels</span>
                    <strong>{panelCountFromKw(row.panel_size_kw)}</strong>
                  </div>
                  <div>
                    <span>Investment</span>
                    <strong>{formatCurrency(row.installation_cost_euro)}</strong>
                  </div>
                  <div>
                    <span>Payback</span>
                    <strong>{row.payback_years}</strong>
                  </div>
                  <div>
                    <span>Coverage</span>
                    <strong>{formatDecimal(row.demand_coverage_pct)}%</strong>
                  </div>
                </div>
                  <div className="rank-score">
                    <span>Decision score</span>
                    <strong>{formatDecimal(row.rankingScore * 100, 0)}</strong>
                  </div>
                </article>
              ))}
            </div>
          </aside>
        </div>
      </div>
    </section>
  );
}
