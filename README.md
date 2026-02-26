# 📈 Energy Trading Pipeline

**Comprehensive energy data ingestion, modeling, and analysis platform**
designed for solar production forecasting, financial viability studies,
and market‑ready data workflows.

This repository implements a **modular pipeline** that automates data
collection, stores time‑series energy data, supports model generation
for energy and financial analysis, and provides tools for exploration
and visualization --- all containerized with Docker.

------------------------------------------------------------------------

## 🧠 What It Does

The **Energy Trading Pipeline** serves as an end‑to‑end environment for:

-   📥 Automating data ingestion from weather, panel specs, and market
    sources\
-   🗄 Managing time‑series energy and market datasets via PostgreSQL\
-   🧩 Orchestrating workflows using Apache Airflow\
-   📊 Analyzing solar production & economic models\
-   🛠 Interactive querying and monitoring via pgAdmin\
-   📈 Visualization and BI dashboards through Metabase

------------------------------------------------------------------------

## 🚀 Key Features

  Capability              Description
  ----------------------- -------------------------------------------
  Airflow Orchestration   Schedule and monitor ETL & modeling tasks
  PostgreSQL Storage      Time‑series and structured data
  Solar Modeling          Hourly, daily, annual kWh estimates
  Financial Analysis      ROI, payback, revenue models
  Containerization        Full Docker environment
  pgAdmin                 Visual DB management
  Metabase                BI dashboards

------------------------------------------------------------------------

## 🗂️ Project Layout
```
Energy-Trading-Pipeline/
├── config/                    # Environment & project configuration
├── dags/                      # Airflow DAG definitions
├── entrypoint/                # Startup scripts for containers
├── postgres/                  # Database init & schema
├── producers/                 # Data ingestion & tasks
├── consumers/                 # Data transformation jobs
├── solar_analysis_data/       # Solar & market datasets
├── dashboard/                 # Metabase / visualization configs
├── docker-compose.yaml        # Orchestration & service definitions
└── README.md
```
------------------------------------------------------------------------

## 🧠 Pipeline Workflow

Raw Weather & Market Data\
→ Q1 Meteorological Analysis\
→ Q2 Production Modeling\
→ Q3 Economic Simulation\
→ Dashboards & Trading Insights

------------------------------------------------------------------------

## 📘 Core Logic

### Q1 --- Meteorological Analysis

Transforms weather data into solar exposure metrics and environmental
risk indices.

### Q2 --- Production Modeling

Converts Q1 outputs into realistic energy production estimates.

### Q3 --- Economic Analysis

Transforms energy into financial metrics: ROI, savings, revenue, payback
time.

------------------------------------------------------------------------

## 🏁 Getting Started

### Requirements

-   Docker\
-   Docker Compose\
-   Python 3.8+

### Installation

``` bash
git clone https://github.com/MatheusSabaudo/Energy-Trading-Pipeline.git
cd Energy-Trading-Pipeline
docker compose up --build
```

------------------------------------------------------------------------

## 📊 Services

  Service    URL
  ---------- -----------------------
  Airflow    http://localhost:8080
  pgAdmin    http://localhost:5050
  Metabase   http://localhost:3000

------------------------------------------------------------------------

## 📈 Example Workflow

1.  Ingest weather/market data\
2.  Run Airflow DAGs\
3.  Generate solar production models\
4.  Store in PostgreSQL\
5.  Visualize in Metabase\
6.  Use outputs for trading/investment decisions

------------------------------------------------------------------------

## 🛠 Development

Add DAGs to `dags/` and restart Airflow containers.

------------------------------------------------------------------------

## 🚀 Deployment

Supports: - External DBs - Secure environment configs - Auth-enabled
Airflow - BI separation - Production orchestration - Admin tooling

------------------------------------------------------------------------

## 📄 License

MIT License --- © 2026 Matheus Sabaudo

------------------------------------------------------------------------

## 🙌 Contributions

Issues and pull requests are welcome.
