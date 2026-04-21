import {
  formatCompactNumber,
  formatCurrency,
  formatDecimal,
  getAnalysisSummary,
  getDagSteps,
  getDataProducts,
  getPipelineStages,
  getStackItems,
  monthLabel,
  type MonthlySummary,
  type ScenarioMetrics,
  type SensitivityRow
} from "../lib/site-data";
import DecisionWorkbench from "../components/decision-workbench";

function SectionHeader({
  eyebrow,
  title,
  description
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="section-header">
      <span className="eyebrow">{eyebrow}</span>
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  );
}

function SummaryMetric({
  label,
  value,
  hint
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <article className="summary-metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{hint}</p>
    </article>
  );
}

function HeroPreview({
  current,
  optimal,
  verdict,
  score
}: {
  current: ScenarioMetrics;
  optimal: ScenarioMetrics;
  verdict: string;
  score: number;
}) {
  const total = current.year_one.annual_load_kwh;
  const coverage = [
    {
      label: "Direct solar usage",
      value: current.year_one.annual_self_consumed_kwh,
      tone: "tone-amber"
    },
    {
      label: "Grid import",
      value: current.year_one.annual_imported_kwh,
      tone: "tone-ink"
    },
    {
      label: "Grid export",
      value: current.year_one.annual_exported_kwh,
      tone: "tone-teal"
    }
  ];

  return (
    <aside className="hero-preview">
      <div className="preview-window">
        <div className="window-bar">
          <div className="window-dots">
            <i />
            <i />
            <i />
          </div>
          <span>executive-dashboard.live</span>
        </div>

        <div className="preview-body">
          <div className="preview-overview">
            <div>
              <span className="eyebrow">Executive readout</span>
              <h3>{verdict}</h3>
              <p>Portfolio-grade view of feasibility, sizing, and pipeline operations.</p>
            </div>
            <div className="score-chip">
              <span>Score</span>
              <strong>{score}/100</strong>
            </div>
          </div>

          <div className="preview-grid">
            <div className="mini-card">
              <span>Current system</span>
              <strong>{formatDecimal(current.panel_size_kw, 1)} kWp</strong>
              <p>{current.payback_display} payback</p>
            </div>
            <div className="mini-card">
              <span>Best tested size</span>
              <strong>{formatDecimal(optimal.panel_size_kw, 1)} kWp</strong>
              <p>{formatCurrency(optimal.npv_25_years_euro)} NPV</p>
            </div>
          </div>

          <div className="balance-preview">
            <div className="balance-head">
              <span>Annual energy balance</span>
              <strong>{formatCompactNumber(current.year_one.annual_production_kwh)} kWh</strong>
            </div>
            <div className="balance-list">
              {coverage.map((item) => (
                <div key={item.label} className="balance-item">
                  <div className="balance-meta">
                    <span>{item.label}</span>
                    <strong>{formatCompactNumber(item.value)} kWh</strong>
                  </div>
                  <div className="balance-track">
                    <div
                      className={`balance-fill ${item.tone}`}
                      style={{ width: `${(item.value / total) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}

function ScenarioCard({
  title,
  caption,
  scenario,
  emphasis
}: {
  title: string;
  caption: string;
  scenario: ScenarioMetrics;
  emphasis: string;
}) {
  return (
    <article className={`scenario-card ${emphasis}`}>
      <div className="scenario-card-head">
        <div>
          <span className="eyebrow">{title}</span>
          <h3>{formatDecimal(scenario.panel_size_kw, 1)} kWp configuration</h3>
        </div>
        <div className="chip">{scenario.payback_display}</div>
      </div>
      <p>{caption}</p>

      <div className="scenario-points">
        <div>
          <span>Annual production</span>
          <strong>{formatCompactNumber(scenario.year_one.annual_production_kwh)} kWh</strong>
        </div>
        <div>
          <span>Demand coverage</span>
          <strong>{formatDecimal(scenario.year_one.demand_coverage_pct)}%</strong>
        </div>
        <div>
          <span>Self-consumption</span>
          <strong>{formatDecimal(scenario.year_one.self_consumption_pct)}%</strong>
        </div>
        <div>
          <span>20-year net profit</span>
          <strong>{formatCurrency(scenario.net_profit_20_years_euro)}</strong>
        </div>
      </div>
    </article>
  );
}

function SeasonalityChart({ data }: { data: MonthlySummary[] }) {
  const maxProduction = Math.max(...data.map((item) => item.production_kwh));
  const maxLoad = Math.max(...data.map((item) => item.load_kwh));
  const maxValue = Math.max(maxProduction, maxLoad);

  return (
    <article className="panel-card">
      <div className="panel-head">
        <div>
          <span className="eyebrow">Seasonality profile</span>
          <h3>Production versus household demand across the year</h3>
        </div>
        <p>Warm months dominate output, but winter still matters for economic resilience and import behavior.</p>
      </div>

      <div className="season-chart">
        {data.map((item) => (
          <div key={item.month} className="season-column">
            <div className="season-bars">
              <div className="season-bar-shell">
                <div
                  className="season-bar production"
                  style={{ height: `${(item.production_kwh / maxValue) * 100}%` }}
                />
              </div>
              <div className="season-bar-shell subtle">
                <div
                  className="season-bar load"
                  style={{ height: `${(item.load_kwh / maxValue) * 100}%` }}
                />
              </div>
            </div>
            <div className="season-meta">
              <strong>{monthLabel(item.month)}</strong>
              <span>{formatDecimal(item.avg_temperature_c)}°C</span>
            </div>
          </div>
        ))}
      </div>

      <div className="legend-row">
        <span>
          <i className="legend-swatch production" />
          Solar production
        </span>
        <span>
          <i className="legend-swatch load" />
          Household load
        </span>
      </div>
    </article>
  );
}

function CashFlowChart({
  current,
  optimal
}: {
  current: ScenarioMetrics;
  optimal: ScenarioMetrics;
}) {
  const values = [...current.cumulative, ...optimal.cumulative];
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const width = 720;
  const height = 280;
  const padding = 28;

  const toPolyline = (series: number[]) =>
    series
      .map((value, index) => {
        const x = padding + (index / (series.length - 1)) * (width - padding * 2);
        const normalized = (value - minValue) / (maxValue - minValue || 1);
        const y = height - padding - normalized * (height - padding * 2);
        return `${x},${y}`;
      })
      .join(" ");

  const zeroY =
    height - padding - ((0 - minValue) / (maxValue - minValue || 1)) * (height - padding * 2);

  return (
    <article className="panel-card">
      <div className="panel-head">
        <div>
          <span className="eyebrow">Economic trajectory</span>
          <h3>Cumulative cash flow over 25 years</h3>
        </div>
        <p>The goal is not just to produce energy, but to understand how capital efficiency evolves over time.</p>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="cashflow-chart" role="img" aria-label="Cash flow comparison">
        <line x1={padding} y1={zeroY} x2={width - padding} y2={zeroY} className="chart-axis" />
        <polyline className="cashflow-line current" points={toPolyline(current.cumulative)} />
        <polyline className="cashflow-line optimal" points={toPolyline(optimal.cumulative)} />
      </svg>

      <div className="legend-row">
        <span>
          <i className="legend-swatch current" />
          Current system
        </span>
        <span>
          <i className="legend-swatch optimal" />
          Best tested size
        </span>
      </div>
    </article>
  );
}

function RecommendationCard({
  current,
  strengths,
  concerns
}: {
  current: ScenarioMetrics;
  strengths: string[];
  concerns: string[];
}) {
  return (
    <article className="panel-card recommendation-card">
      <div className="panel-head">
        <div>
          <span className="eyebrow">Recommendation logic</span>
          <h3>Why the answer is positive, but not blindly aggressive</h3>
        </div>
      </div>

      <div className="recommendation-stats">
        <div>
          <span>Production / load</span>
          <strong>{formatDecimal(current.year_one.production_coverage_pct)}%</strong>
        </div>
        <div>
          <span>Self-consumption</span>
          <strong>{formatDecimal(current.year_one.self_consumption_pct)}%</strong>
        </div>
        <div>
          <span>Break-even rate</span>
          <strong>{formatDecimal(current.break_even_rate_euro_per_kwh, 2)} €/kWh</strong>
        </div>
      </div>

      <div className="insight-columns">
        <div>
          <h4>Strengths</h4>
          <ul>
            {strengths.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4>Concerns</h4>
          <ul className="caution-list">
            {concerns.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
}

function SensitivityTable({ rows }: { rows: SensitivityRow[] }) {
  return (
    <article className="panel-card table-card">
      <div className="panel-head">
        <div>
          <span className="eyebrow">Sensitivity analysis</span>
          <h3>Sizing trade-offs at a glance</h3>
        </div>
        <p>Professional decision support means showing the trade space, not just highlighting a single answer.</p>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Size</th>
              <th>Annual output</th>
              <th>Self-consumption</th>
              <th>Demand coverage</th>
              <th>Cost</th>
              <th>Payback</th>
              <th>NPV</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.panel_size_kw}>
                <td>{formatDecimal(row.panel_size_kw, 1)} kWp</td>
                <td>{formatCompactNumber(row.annual_production_kwh)} kWh</td>
                <td>{formatDecimal(row.self_consumption_pct)}%</td>
                <td>{formatDecimal(row.demand_coverage_pct)}%</td>
                <td>{formatCurrency(row.installation_cost_euro)}</td>
                <td>{row.payback_years}</td>
                <td>{formatCurrency(row.npv_25_years_euro)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}

function PipelineSection() {
  const stages = getPipelineStages();
  const dagSteps = getDagSteps();
  const stackItems = getStackItems();
  const dataProducts = getDataProducts();

  return (
    <section id="pipeline" className="content-section">
      <SectionHeader
        eyebrow="Pipeline narrative"
        title="A polished front-end, backed by a real data engineering backbone"
        description="This website is intentionally structured like a technical product story: source systems, orchestration, medallion layers, and analytical serving all connect to the solar decision surface."
      />

      <div className="pipeline-layout">
        <div className="pipeline-timeline">
          {stages.map((stage, index) => (
            <article key={stage.title} className="timeline-card">
              <div className="timeline-top">
                <span className="timeline-index">0{index + 1}</span>
                <h3>{stage.title}</h3>
              </div>
              <p>{stage.summary}</p>
              <ul>
                {stage.details.map((detail) => (
                  <li key={detail}>{detail}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>

        <div className="pipeline-sidebar">
          <article className="side-card">
            <span className="eyebrow">Airflow chain</span>
            <ol>
              {dagSteps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </article>

          <article className="side-card">
            <span className="eyebrow">Stack</span>
            <div className="tag-list">
              {stackItems.map((item) => (
                <span key={item} className="tag">
                  {item}
                </span>
              ))}
            </div>
          </article>

          <article className="side-card">
            <span className="eyebrow">Data products</span>
            <div className="tag-list muted">
              {dataProducts.map((item) => (
                <span key={item} className="tag muted">
                  {item}
                </span>
              ))}
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}

function ProjectStorySection() {
  const pillars = [
    {
      title: "Project scope",
      copy:
        "This project brings together ingestion, streaming, storage, orchestration, simulation, analytics, and web delivery inside one cohesive system.",
      bullets: [
        "Combines modern frameworks with an end-to-end data workflow.",
        "Moves beyond isolated exercises into a structured system with realistic trade-offs.",
        "Uses real weather context plus a calibrated Turin solar simulation instead of toy placeholder data."
      ]
    },
    {
      title: "Technical depth",
      copy:
        "The most valuable outcome is not only the final interface, but also the technical depth behind it: debugging, iteration, reliability, and reproducibility across the stack.",
      bullets: [
        "Models data from source to bronze, silver, and gold layers.",
        "Builds reproducible analysis instead of relying on notebook state.",
        "Connects backend data engineering work to a polished product surface."
      ]
    },
    {
      title: "Walkthrough topics",
      copy:
        "The website is structured to support a clear walkthrough of the architectural decisions, the simulation logic, the recommendation trade-offs, and the practical engineering lessons in the project.",
      bullets: [
        "Kafka, PostgreSQL, Airflow, data quality, and medallion architecture.",
        "Solar modeling assumptions, economics, sensitivity analysis, and decision logic.",
        "Next.js/Vercel delivery, UX thinking, and how technical output is framed for users."
      ]
    }
  ];

  return (
    <section id="project-story" className="content-section">
      <SectionHeader
        eyebrow="Project overview"
        title="A complete project walkthrough, not just a dashboard screen"
        description="The site is designed to present the project clearly: real data, multiple frameworks, simulation logic, pipeline architecture, and a user-facing decision layer in one coherent flow."
      />

      <div className="story-grid">
        {pillars.map((pillar) => (
          <article key={pillar.title} className="story-card">
            <span className="eyebrow">{pillar.title}</span>
            <p>{pillar.copy}</p>
            <ul>
              {pillar.bullets.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}

export default function HomePage() {
  const summary = getAnalysisSummary();
  const current = summary.current_system;
  const optimal = summary.optimal_system;

  const executiveMetrics = [
    {
      label: "Annual production",
      value: `${formatCompactNumber(current.year_one.annual_production_kwh)} kWh`,
      hint: "Current calibrated 3.0 kWp baseline for Turin"
    },
    {
      label: "Current payback",
      value: current.payback_display,
      hint: "Based on modeled load matching and price assumptions"
    },
    {
      label: "Best-tested NPV",
      value: formatCurrency(optimal.npv_25_years_euro),
      hint: "Highest 25-year value across the sizing sweep"
    },
    {
      label: "Direct demand coverage",
      value: `${formatDecimal(current.year_one.demand_coverage_pct)}%`,
      hint: "Solar share used directly by the household"
    }
  ];

  return (
    <main className="site-shell">
      <header className="site-header">
        <div className="brand">
          <span className="brand-kicker">End-to-end project walkthrough</span>
          <strong>Solar decision platform, simulation engine, and data pipeline</strong>
        </div>
        <nav className="main-nav">
          <a href="#project-story">Project</a>
          <a href="#analysis">Analysis</a>
          <a href="#pipeline">Pipeline</a>
        </nav>
      </header>

      <section className="hero-section">
        <div className="hero-copy">
          <span className="eyebrow">Decision platform + engineering case study</span>
          <h1>
            A decision-driven solar intelligence project designed to compare solar against the traditional energy model.
          </h1>
          <p>
            The project combines data engineering workflows, backend logic, simulation, analytics, and modern web
            delivery. The result is a decision helper that shows how much can be saved, how solar compares to a
            traditional grid-only setup, and which scenario is strongest under different business constraints.
          </p>

          <div className="hero-actions">
            <a className="button primary" href="#analysis">
              Open the analysis
            </a>
            <a className="button secondary" href="#pipeline">
              Review architecture
            </a>
          </div>

          <div className="hero-meta">
            <span>Verdict: {summary.verdict}</span>
            <span>Score: {summary.score}/100</span>
            <span>Updated: {new Date(summary.generated_at).toLocaleString("en-US")}</span>
          </div>
        </div>

        <HeroPreview current={current} optimal={optimal} verdict={summary.verdict} score={summary.score} />
      </section>

      <section className="metrics-grid">
        {executiveMetrics.map((metric) => (
          <SummaryMetric key={metric.label} label={metric.label} value={metric.value} hint={metric.hint} />
        ))}
      </section>

      <ProjectStorySection />

      <section id="analysis" className="content-section">
        <SectionHeader
          eyebrow="Executive analysis"
          title="The product surface: a decision room for clients, companies, and advisory conversations"
          description="This is the user-facing layer of the project: clear recommendation logic, scenario steering, transparent trade-offs, and a direct comparison between solar and the traditional energy path."
        />

        <DecisionWorkbench current={current} optimal={optimal} sensitivity={summary.sensitivity} />

        <div className="scenario-grid">
          <ScenarioCard
            title="Current recommendation"
            caption="The configured residential baseline is financially solid and easy to defend when the buyer values a disciplined capex and a balanced payback profile."
            scenario={current}
            emphasis="neutral"
          />
          <ScenarioCard
            title="Best tested system"
            caption="The larger configuration creates stronger lifetime value, but it also pushes self-consumption down, which is exactly the kind of trade-off a proper advisory tool should expose."
            scenario={optimal}
            emphasis="highlight"
          />
        </div>

        <div className="analysis-grid">
          <SeasonalityChart data={summary.monthly_summary} />
          <RecommendationCard current={current} strengths={summary.strengths} concerns={summary.concerns} />
        </div>

        <div className="analysis-grid wide">
          <CashFlowChart current={current} optimal={optimal} />
          <SensitivityTable rows={summary.sensitivity} />
        </div>
      </section>

      <PipelineSection />
    </main>
  );
}
