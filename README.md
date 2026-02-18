# 📈 Energy Trading Pipeline

A modular **data ingestion & processing pipeline** designed to support
energy trading analysis and forecasting workflows.\
This repository combines **workflow orchestration (Airflow)**,
**database support (PostgreSQL)**, and **data analysis for solar and
trading signals** into a containerized environment.

------------------------------------------------------------------------

## 🧠 Project Overview

The **Energy Trading Pipeline** provides a structured ecosystem to:

-   Automate data ingestion from energy sources (e.g., solar production,
    market feeds)
-   Store and manage time‑series energy data using PostgreSQL
-   Orchestrate repeatable workflows using **Apache Airflow**
-   Generate analysis datasets for downstream trading models or
    dashboards

------------------------------------------------------------------------

## 🚀 Features

✅ Airflow‑based orchestration\
✅ PostgreSQL integration\
✅ Solar data analysis pipeline\
✅ Containerized deployment

------------------------------------------------------------------------

## 🗂️ Repository Structure

    📦Energy‑Trading‑Pipeline
    ├── config/
    ├── dags/
    ├── entrypoint/
    ├── postgres/
    ├── solar_analysis_data/
    ├── docker‑compose.yaml
    └── README.md

------------------------------------------------------------------------

## 🧪 Prerequisites

-   Docker\
-   Docker Compose\
-   Python 3.8+

------------------------------------------------------------------------

## 🏁 Getting Started

### Clone the repository

``` sh
git clone https://github.com/MatheusSabaudo/Energy-Trading-Pipeline.git
cd Energy-Trading-Pipeline
```

### Start services

``` sh
docker compose up --build
```

------------------------------------------------------------------------

## 📌 Airflow

Access UI at:\
`http://localhost:8080`

------------------------------------------------------------------------

## 📊 Solar & Trading Analyses

The `solar_analysis_data/` directory is intended for:

-   Solar production datasets\
-   Market price data\
-   Model training data\
-   Forecasting outputs

------------------------------------------------------------------------

## 🛠️ Development

Add new DAGs inside `dags/` and restart Airflow.

------------------------------------------------------------------------

## 📦 Deployment

Supports staging and production with:

-   Secure env configs
-   External DB
-   Auth-enabled Airflow
-   Container orchestration

------------------------------------------------------------------------

## 📄 License

MIT License --- © 2026 Matheus Sabaudo

------------------------------------------------------------------------

## 📬 Contributions

Issues and pull requests are welcome.
