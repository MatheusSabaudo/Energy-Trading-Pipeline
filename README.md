# 📈 Energy Trading Pipeline

Comprehensive energy data ingestion, modeling, and analysis platform
designed for solar production forecasting, financial viability studies,
and market‑ready data workflows.

------------------------------------------------------------------------

## 🧠 What It Does

The Energy Trading Pipeline is an end‑to‑end environment for: -
Automating data ingestion from weather, panel specs, and market
sources - Managing time‑series energy and market datasets via
PostgreSQL - Orchestrating workflows using Apache Airflow - Analyzing
solar production & economic models - Interactive querying via pgAdmin -
Visualization and BI dashboards through Metabase

------------------------------------------------------------------------

## 🚀 Key Features

-   Airflow Orchestration\
-   PostgreSQL Storage\
-   Solar Production Modeling\
-   Economic & Financial Analysis\
-   Containerized Development\
-   pgAdmin UI\
-   Metabase Dashboards

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
```
Raw Weather & Market Data
        ↓
Preprocessing & Classification (Q1)
        ↓
Solar Production Modeling (Q2)
        ↓
Economic & Financial Simulation (Q3)
        ↓
Dashboards & Exportable Metrics
```

------------------------------------------------------------------------

## 🏁 Getting Started

Requirements: - Docker - Docker Compose - Python 3.8+
```
Clone & Run: git clone
https://github.com/MatheusSabaudo/Energy-Trading-Pipeline.git\
cd Energy-Trading-Pipeline\
docker compose up --build
```

------------------------------------------------------------------------

## 📊 Services

Airflow: http://localhost:8080\
pgAdmin: http://localhost:5050\
Metabase: http://localhost:3000

------------------------------------------------------------------------

## 📄 License

MIT License --- © 2026 Matheus Sabaudo
