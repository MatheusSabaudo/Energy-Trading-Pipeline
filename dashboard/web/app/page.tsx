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

const ARCHITECTURE_DIAGRAM = String.raw`
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                ┌─────────────────┴─────────────────┐
                ▼                                   ▼
  ┌───────────────────────┐             ┌───────────────────────┐
  │   WEATHERSTACK API    │             │   IOT SIMULATOR       │
  │   (weatherstack.com)  │             │   (Kafka Producer)    │
  └───────────┬───────────┘             └───────────┬───────────┘
              │                                     │
              ▼                                     ▼
      ┌───────────────┐                     ┌───────────────┐
      │  Python Fetch │                     │    Kafka      │
      │   (hourly)    │                     │  (solar-raw)  │
      └───────┬───────┘                     └───────┬───────┘
              │                                     │
              └────────────────────┬────────────────┘
                                   ▼
                      ┌─────────────────────────┐
                      │        PostgreSQL       │
                      │       (solar_data)      │
                      └─────────────┬───────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            ┌───────────────┐               ┌───────────────┐
            │ weather_data  │               │  solar_panel  │
            │   (Bronze)    │               │    readings   │
            └───────┬───────┘               └───────┬───────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │        Apache Airflow         │
                    │      (Orchestration Layer)    │
                    │  ┌─────────────────────────┐  │
                    │  │ 02_silver_transform_dag │  │
                    │  │ 03_gold_load_dag        │  │
                    │  │ 04_anomaly_detection_dag│  │
                    │  └─────────────────────────┘  │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        ┌───────────────────┐             ┌─────────────────────┐
        │   Silver Layer    │             │    Gold Layer       │
        │  (Cleaned Data)   │             │ (Aggregated Data)   │
        │ - silver_weather  │             │ - gold_daily_panel  │
        │ - silver_solar    │             │ - gold_hourly_      │
        └───────────────────┘             │   system            │
                                          │ - gold_monthly_kpis │
                                          │ - gold_anomalies    │
                                          └─────────────────────┘
                                                      │
                                                      ▼
                                            ┌───────────────────┐
                                            │    Monitoring     │
                                            │    & Alerts       │
                                            └───────────────────┘
`;

const PROJECT_TREE = String.raw`
Energy-Trading-Pipeline/
│
├── config/
│   └── userdata_config.py
├── ingestion/
│   ├── api/
│   │   └── weatherstack_fetcher.py
│   ├── iot/
│   │   ├── solar_producer.py
│   │   └── iot_to_postgres.py
│   └── scripts/
│       └── create-topics.sh
├── postgres/
│   ├── init/
│   │   └── init.sql
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── orchestration/
│   ├── dags/
│   │   ├── 01_ingestion_dag.py
│   │   ├── 02_silver_transform_dag.py
│   │   ├── 03_gold_load_dag.py
│   │   ├── 04_anomaly_detection_dag.py
│   │   └── 05_pipeline_monitor_dag.py
│   └── scripts/
├── monitoring/
├── solar_analysis_data/
│   ├── turin_model.py
│   ├── reliable_analysis.py
│   └── notebooks_output/
├── dashboard/
│   ├── powerbi/
│   └── web/
├── docker-compose.yml
├── requirements.txt
└── README.md
`;

const FRAMEWORKS = [
  {
    title: "Python",
    role: "Core application logic",
    copy:
      "Python drives the WeatherStack ingestion, the IoT simulator, the reliable Turin solar model, and the economic analysis pipeline.",
    bullets: [
      "API fetchers and streaming producers",
      "Reproducible simulation and analysis scripts",
      "Project-wide configuration and tests"
    ]
  },
  {
    title: "Apache Kafka",
    role: "Streaming boundary",
    copy:
      "Kafka separates event generation from persistence, which makes the ingestion story feel like a real streaming system instead of a direct script-to-database load.",
    bullets: [
      "Solar panel events published by the simulator",
      "Consumer persists raw records into bronze tables",
      "Useful for explaining decoupling in interviews"
    ]
  },
  {
    title: "PostgreSQL",
    role: "Operational and analytical storage",
    copy:
      "PostgreSQL holds the medallion layers and gives the project a concrete data-modeling backbone through raw, cleaned, and aggregated tables.",
    bullets: [
      "Bronze raw landing tables",
      "Silver validation and enrichment layer",
      "Gold KPI, hourly, daily, and anomaly outputs"
    ]
  },
  {
    title: "Apache Airflow",
    role: "Orchestration",
    copy:
      "Airflow turns the scripts and SQL into a scheduled pipeline with explicit stages, DAG dependencies, and monitoring-friendly execution boundaries.",
    bullets: [
      "Ingestion orchestration",
      "Silver and gold transformations",
      "Anomaly detection and pipeline monitoring"
    ]
  },
  {
    title: "Docker Compose",
    role: "Local platform environment",
    copy:
      "Docker Compose makes the project reproducible by packaging Kafka, PostgreSQL, Airflow, and supporting services into a single runnable environment.",
    bullets: [
      "Multi-service local stack",
      "Consistent environment for demos",
      "Clear project setup story"
    ]
  },
  {
    title: "Next.js + Vercel",
    role: "Portfolio presentation layer",
    copy:
      "The website is the presentation surface of the project: it explains architecture, shows outputs, and turns the repository into something easy to walk through live.",
    bullets: [
      "Static project portfolio site",
      "Reads generated JSON outputs",
      "Structured for interview walkthroughs"
    ]
  }
];

const PORTFOLIO_SECTIONS = [
  {
    title: "What the project does",
    copy:
      "This repository combines streaming ingestion, medallion modeling, orchestration, monitoring, and a solar feasibility analysis for Turin inside one end-to-end system."
  },
  {
    title: "Why this site exists",
    copy:
      "The website is not meant to be a product demo for external clients anymore. It is meant to explain the repository clearly during interviews: architecture, framework choices, data flow, and outputs."
  },
  {
    title: "What can be explained live",
    copy:
      "The site is structured to support a walkthrough of the pipeline, the solar simulation, the reliability fixes, and the way raw data becomes something decision-ready."
  }
];

const ENGINEERING_NOTES = [
  "The original notebook flow was analyzed and replaced with a reproducible Python pipeline.",
  "Turin weather and solar output were turned into a calibrated yearly simulation instead of relying on sparse notebook-state results.",
  "The website reads generated artifacts so the portfolio surface stays tied to real project outputs."
];

const ROLE_LENSES = [
  {
    title: "Data Engineer",
    points: [
      "Streaming ingestion with Kafka and consumer persistence into bronze tables",
      "Medallion architecture across bronze, silver, and gold layers",
      "Airflow DAG orchestration, SQL transformations, and data quality logic"
    ]
  },
  {
    title: "Cloud Engineer",
    points: [
      "The current local architecture can be re-designed as an AWS-based target architecture using managed services",
      "This creates a strong cloud solutions narrative around service selection, reliability, observability, and scalability",
      "The portfolio can be used to explain how the same project would be implemented in a real AWS environment"
    ]
  }
];

const AWS_MAPPING = [
  {
    area: "Streaming and ingestion",
    services: "Amazon MSK / Kinesis, Lambda or ECS, API Gateway",
    explanation: "The current Kafka and Python ingestion story can be translated into a managed AWS ingestion layer."
  },
  {
    area: "Storage and modeling",
    services: "Amazon RDS PostgreSQL, Amazon S3, AWS Glue Data Catalog",
    explanation: "The bronze, silver, and gold pattern can be re-explained as a managed storage and catalog architecture."
  },
  {
    area: "Orchestration and scheduling",
    services: "Amazon MWAA, EventBridge, Step Functions",
    explanation: "The Airflow DAG structure creates a natural bridge to AWS-native orchestration discussions."
  },
  {
    area: "Monitoring and serving",
    services: "CloudWatch, SNS, QuickSight, Vercel or Amplify",
    explanation: "Monitoring, alerting, and presentation can be explained as an end-to-end cloud operations layer."
  }
];

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

function PortfolioPreview({
  dagSteps,
  stackItems,
  dataProducts,
  simulationYear,
  location
}: {
  dagSteps: string[];
  stackItems: string[];
  dataProducts: string[];
  simulationYear: number;
  location: string;
}) {
  return (
    <aside className="hero-preview">
      <div className="preview-window">
        <div className="window-bar">
          <div className="window-dots">
            <i />
            <i />
            <i />
          </div>
          <span>project-walkthrough.vercel.app</span>
        </div>

        <div className="preview-body">
          <div className="preview-overview">
            <div>
              <span className="eyebrow">Project snapshot</span>
              <h3>Architecture, simulation, and serving</h3>
              <p>One repository used to explain ingestion, modeling, orchestration, and analytics outputs.</p>
            </div>
            <div className="score-chip">
              <span>Location</span>
              <strong>{location}</strong>
            </div>
          </div>

          <div className="preview-grid">
            <div className="mini-card">
              <span>Frameworks</span>
              <strong>{stackItems.length}</strong>
              <p>Python, Kafka, PostgreSQL, Airflow, Docker, Next.js</p>
            </div>
            <div className="mini-card">
              <span>DAG chain</span>
              <strong>{dagSteps.length} stages</strong>
              <p>From ingestion through monitoring</p>
            </div>
          </div>

          <div className="balance-preview">
            <div className="balance-head">
              <span>Repository narrative</span>
              <strong>{simulationYear} simulation outputs</strong>
            </div>
            <div className="balance-list">
              <div className="balance-item">
                <div className="balance-meta">
                  <span>Medallion products</span>
                  <strong>{dataProducts.length}</strong>
                </div>
                <div className="balance-track">
                  <div className="balance-fill tone-amber" style={{ width: "100%" }} />
                </div>
              </div>
              <div className="balance-item">
                <div className="balance-meta">
                  <span>Analysis layer</span>
                  <strong>Reliable Turin model</strong>
                </div>
                <div className="balance-track">
                  <div className="balance-fill tone-teal" style={{ width: "82%" }} />
                </div>
              </div>
              <div className="balance-item">
                <div className="balance-meta">
                  <span>Presentation layer</span>
                  <strong>Next.js portfolio site</strong>
                </div>
                <div className="balance-track">
                  <div className="balance-fill tone-ink" style={{ width: "74%" }} />
                </div>
              </div>
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
          <span className="eyebrow">Solar analysis</span>
          <h3>Production versus household demand across the year</h3>
        </div>
        <p>This chart is one of the clearest ways to explain how the Turin simulation behaves season by season.</p>
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
        <p>This output makes the financial story concrete and easy to explain visually during a walkthrough.</p>
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
          <span className="eyebrow">What the analysis proves</span>
          <h3>From raw data to something financially explainable</h3>
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
          <span className="eyebrow">Sizing sweep</span>
          <h3>How the solar model behaves across tested system sizes</h3>
        </div>
        <p>The portfolio site keeps one analytical table on the page so the project can be explained with real outputs.</p>
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

function ArchitectureSection() {
  const dagSteps = getDagSteps();
  const stages = getPipelineStages();
  const dataProducts = getDataProducts();

  return (
    <section id="architecture" className="content-section">
      <SectionHeader
        eyebrow="Architecture"
        title="The root README diagram is part of the portfolio story"
        description="The homepage now uses the architecture diagram from the repository itself so the project explanation stays grounded in the actual structure of the codebase."
      />

      <div className="architecture-layout">
        <article className="panel-card code-panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">README diagram</span>
              <h3>System flow from sources to gold outputs</h3>
            </div>
          </div>
          <pre className="ascii-diagram">
            <code>{ARCHITECTURE_DIAGRAM}</code>
          </pre>
        </article>

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
            <span className="eyebrow">Pipeline chapters</span>
            <ul>
              {stages.map((stage) => (
                <li key={stage.title}>
                  <strong>{stage.title}:</strong> {stage.summary}
                </li>
              ))}
            </ul>
          </article>

          <article className="side-card">
            <span className="eyebrow">Gold-facing products</span>
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

function FrameworkSection() {
  return (
    <section id="frameworks" className="content-section">
      <SectionHeader
        eyebrow="Frameworks"
        title="Each framework has a clear job in the project"
        description="The site now explains the stack as implementation choices, not just a list of technologies. That makes the walkthrough much stronger during interviews."
      />

      <div className="framework-grid">
        {FRAMEWORKS.map((item) => (
          <article key={item.title} className="framework-card">
            <span className="eyebrow">{item.role}</span>
            <h3>{item.title}</h3>
            <p>{item.copy}</p>
            <ul>
              {item.bullets.map((bullet) => (
                <li key={bullet}>{bullet}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}

function RoleSection() {
  return (
    <section id="roles" className="content-section">
      <SectionHeader
        eyebrow="Interview angles"
        title="One project, two role narratives"
        description="The same repository can be presented in two different ways: as the current data engineering implementation, and as the cloud-engineering version of the same system redesigned for AWS."
      />

      <div className="framework-grid">
        {ROLE_LENSES.map((role) => (
          <article key={role.title} className="framework-card">
            <span className="eyebrow">Role lens</span>
            <h3>{role.title}</h3>
            <ul>
              {role.points.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}

function AwsSection() {
  return (
    <section id="aws" className="content-section">
      <SectionHeader
        eyebrow="AWS target architecture"
        title="This section is the cloud-engineering version of the same project"
        description="The current repository uses the local stack that was built for the actual implementation. This section is reserved for the AWS version, where the same architecture is reimagined with managed AWS services."
      />

      <div className="architecture-layout">
        <article className="panel-card code-panel aws-placeholder">
          <div className="panel-head">
            <div>
              <span className="eyebrow">AWS architecture diagram</span>
              <h3>Reserved space for the AWS implementation diagram</h3>
            </div>
          </div>
          <div className="aws-placeholder-box">
            <strong>Place the AWS diagram here</strong>
            <p>
              This section is designed for the AWS target-state architecture of the project, so the same portfolio can
              support cloud engineering interviews using the managed-services version of the system.
            </p>
          </div>
        </article>

        <div className="pipeline-sidebar">
          <article className="side-card">
            <span className="eyebrow">How to talk through it</span>
            <ul>
              <li>Start from the current working implementation and explain which frameworks would be replaced by AWS services.</li>
              <li>Use the same pipeline stages to discuss scalability, resilience, security, observability, and service boundaries.</li>
              <li>Position the AWS diagram as the cloud implementation of the same project, not as a separate idea.</li>
            </ul>
          </article>

          <article className="side-card">
            <span className="eyebrow">AWS service mapping</span>
            <div className="aws-map">
              {AWS_MAPPING.map((item) => (
                <div key={item.area} className="aws-map-card">
                  <strong>{item.area}</strong>
                  <span>{item.services}</span>
                  <p>{item.explanation}</p>
                </div>
              ))}
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}

function StructureSection() {
  return (
    <section id="structure" className="content-section">
      <SectionHeader
        eyebrow="Repository structure"
        title="The website also explains how the repository is organized"
        description="Showing the project structure directly on the site makes it much easier to walk through where ingestion, SQL, orchestration, analysis, and front-end work live."
      />

      <div className="structure-layout">
        <article className="panel-card code-panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">Project tree</span>
              <h3>Top-level repository map</h3>
            </div>
          </div>
          <pre className="ascii-diagram">
            <code>{PROJECT_TREE}</code>
          </pre>
        </article>

        <div className="story-grid">
          {PORTFOLIO_SECTIONS.map((section) => (
            <article key={section.title} className="story-card">
              <span className="eyebrow">{section.title}</span>
              <p>{section.copy}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function AnalysisSection({
  current,
  optimal,
  strengths,
  concerns,
  monthlySummary,
  sensitivity
}: {
  current: ScenarioMetrics;
  optimal: ScenarioMetrics;
  strengths: string[];
  concerns: string[];
  monthlySummary: MonthlySummary[];
  sensitivity: SensitivityRow[];
}) {
  return (
    <section id="analysis" className="content-section">
      <SectionHeader
        eyebrow="Solar chapter"
        title="The solar analysis is one chapter of the full project"
        description="This section shows the outputs generated by the reliable Turin simulation. It proves that the repository is not only a pipeline exercise, but also a real analytical project with interpretable results."
      />

      <div className="scenario-grid">
        <ScenarioCard
          title="Current baseline"
          caption="The 3.0 kWp system is the configured baseline used to explain the starting point of the economic and production analysis."
          scenario={current}
          emphasis="neutral"
        />
        <ScenarioCard
          title="Best tested size"
          caption="The sizing sweep is useful in the portfolio because it shows how the project moves from simulation into real trade-off analysis."
          scenario={optimal}
          emphasis="highlight"
        />
      </div>

      <div className="analysis-grid">
        <SeasonalityChart data={monthlySummary} />
        <RecommendationCard current={current} strengths={strengths} concerns={concerns} />
      </div>

      <div className="analysis-grid wide">
        <CashFlowChart current={current} optimal={optimal} />
        <SensitivityTable rows={sensitivity} />
      </div>
    </section>
  );
}

export default function HomePage() {
  const summary = getAnalysisSummary();
  const current = summary.current_system;
  const optimal = summary.optimal_system;
  const dagSteps = getDagSteps();
  const stackItems = getStackItems();
  const dataProducts = getDataProducts();

  const executiveMetrics = [
    {
      label: "Frameworks used",
      value: `${stackItems.length}`,
      hint: "Python, Kafka, PostgreSQL, Airflow, Docker, and Next.js/Vercel"
    },
    {
      label: "Airflow stages",
      value: `${dagSteps.length}`,
      hint: "Explicit DAG chain from ingestion to monitoring"
    },
    {
      label: "Data products",
      value: `${dataProducts.length}`,
      hint: "Bronze, silver, and gold analytical tables"
    },
    {
      label: "Turin baseline",
      value: `${formatCompactNumber(current.year_one.annual_production_kwh)} kWh`,
      hint: "Reliable annual production for the calibrated 3.0 kWp system"
    }
  ];

  return (
    <main className="site-shell">
      <header className="site-header">
        <div className="brand">
          <span className="brand-kicker">Project portfolio</span>
          <strong>Solar energy data pipeline and feasibility analysis</strong>
        </div>
        <nav className="main-nav">
          <a href="#roles">Roles</a>
          <a href="#architecture">Architecture</a>
          <a href="#aws">AWS</a>
          <a href="#frameworks">Frameworks</a>
          <a href="#structure">Structure</a>
          <a href="#analysis">Analysis</a>
        </nav>
      </header>

      <section className="hero-section">
        <div className="hero-copy">
          <span className="eyebrow">End-to-end data engineering project</span>
          <h1>A portfolio website built to explain the full project, not just show a dashboard.</h1>
          <p>
            This website now presents the repository as a complete project walkthrough: the architecture from the root
            README, the frameworks used across each layer, the repository structure, and the solar analysis outputs that
            sit on top of the pipeline.
          </p>

          <div className="hero-actions">
            <a className="button primary" href="#architecture">
              View architecture
            </a>
            <a className="button secondary" href="#analysis">
              Open analysis chapter
            </a>
          </div>

          <div className="hero-meta">
            <span>Simulation year: {summary.simulation_year}</span>
            <span>Location: {summary.location.city}</span>
            <span>Updated: {new Date(summary.generated_at).toLocaleString("en-US")}</span>
          </div>
        </div>

        <PortfolioPreview
          dagSteps={dagSteps}
          stackItems={stackItems}
          dataProducts={dataProducts}
          simulationYear={summary.simulation_year}
          location={summary.location.city}
        />
      </section>

      <section className="metrics-grid">
        {executiveMetrics.map((metric) => (
          <SummaryMetric key={metric.label} label={metric.label} value={metric.value} hint={metric.hint} />
        ))}
      </section>

      <section className="content-section">
        <SectionHeader
          eyebrow="Project framing"
          title="The site is now structured as a reusable interview walkthrough"
          description="Instead of behaving like a client-facing product demo, the homepage now explains what was built, how the repository is organized, which frameworks were used, and how the same project can support different interview narratives."
        />

        <div className="story-grid">
          {PORTFOLIO_SECTIONS.map((item) => (
            <article key={item.title} className="story-card">
              <span className="eyebrow">{item.title}</span>
              <p>{item.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <RoleSection />
      <ArchitectureSection />
      <AwsSection />
      <FrameworkSection />
      <StructureSection />

      <section className="content-section">
        <SectionHeader
          eyebrow="Engineering notes"
          title="A few key improvements made the project explainable and reliable"
          description="These points are useful during interviews because they show iteration, debugging, and judgment instead of only the final UI."
        />

        <div className="framework-grid compact">
          {ENGINEERING_NOTES.map((note) => (
            <article key={note} className="framework-card compact">
              <p>{note}</p>
            </article>
          ))}
        </div>
      </section>

      <AnalysisSection
        current={current}
        optimal={optimal}
        strengths={summary.strengths}
        concerns={summary.concerns}
        monthlySummary={summary.monthly_summary}
        sensitivity={summary.sensitivity}
      />
    </main>
  );
}
