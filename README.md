# 📈 Energy Trading Pipeline

A modular **data ingestion & processing pipeline** designed to support energy trading analysis and forecasting workflows.
This repository combines **workflow orchestration (Airflow)**, **database support (PostgreSQL)**, **data analysis for solar and trading signals**, and **data visualization & management tools** into a containerized environment.

---

## 🧠 Project Overview

The **Energy Trading Pipeline** provides a structured ecosystem to:

* Automate data ingestion from energy sources (e.g., solar production, market feeds)
* Store and manage time‑series energy data using PostgreSQL
* Orchestrate repeatable workflows using **Apache Airflow**
* Generate analysis datasets for downstream trading models or dashboards
* Query and manage databases visually via **pgAdmin**
* Visualize and explore data through **Metabase dashboards**

---

## 🚀 Features

```
✅ Airflow‑based orchestration
✅ PostgreSQL integration
✅ Solar data analysis pipeline
✅ Containerized deployment
✅ pgAdmin database management
✅ Metabase BI dashboards & visual analytics
```

---

## 🗂️ Repository Structure

```
📦Energy‑Trading‑Pipeline
├── config/
├── dags/
├── entrypoint/
├── postgres/
├── solar_analysis_data/
├── docker‑compose.yaml
└── README.md
```

---

## 📘 CORE PROJECT LOGIC – STRUCTURE & ANALYSIS ROADMAP

> **This section represents the heart of the project.**
> It documents the full scientific, technical, and financial modeling logic behind the pipeline, describing how raw data is transformed into production estimates, financial metrics, and investment insights.

---

## Step 0 – Configuration & Research

Before running simulations, define **system and panel parameters**:

* **Panel spacing** – prevent shading between panels.
* **Cloud cover, UV index, wind speed ranges** – used for categorization.
* **Battery size** – estimate storage requirements for worst-case scenarios.
* **Panel parameters** – type (Polycrystalline, Monocrystalline, PERC, Experimental) and efficiency.

These parameters feed directly into production and financial calculations.

---

## Step 1 – Q1: Preliminary Meteorological Analysis

**Goal:** Understand the environmental conditions affecting solar production.

**Inputs:** Temperature, cloud cover, UV index, wind speed, solar angle, solar potential.

**Outcome:** Q1 converts raw weather data into **solar exposure metrics and environmental risk factors**.

---

## Step 2 – Q2: Production Modeling

**Goal:** Convert Q1 metrics into **hourly, daily, and monthly kWh production**.

**Outcome:** Q2 produces realistic energy output estimates considering environmental factors, panel specs, and system losses.

---

## Step 3 – Q3: Economic & Financial Analysis

**Goal:** Translate energy production into **financial metrics**.

**Outcome:** Q3 transforms energy production into **financial insight**, guiding investment decisions.

---

## Step 4 – Full Pipeline Flow

**Summary Flowchart:**

```
Raw Weather Data (Q1)
        ↓
Preprocessing & Classification → Solar Potential, Cloud, UV, Wind, Angle
        ↓
Hourly & Aggregated Production (Q2)
        ↓
Apply System Losses & Derating → Daily, Monthly, Annual kWh
        ↓
Economic Simulation (Q3)
        ↓
Self-Consumption, Grid Injection, Incentives → Savings & Revenue
        ↓
Long-Term Cash Flow & ROI → Investment Decision
```

---

## 🌐 Future Work – Interactive Website Dashboard

Future extension: create a **web-based dashboard hosted on GitHub Pages** to visualize all pipeline outputs.

**Key Features:**

* Overview dashboard
* Technical Sheet (Scheda Tecnica)
* Interactive graphs
* Scenario testing interface
* Static deployment using JSON/CSV from `solar_analysis_data/`

**Benefit:** Users can explore energy production, financial scenarios, and technical calculations **without running Python scripts locally**.


---

## 🧪 Prerequisites

* Docker
* Docker Compose
* Python 3.8+

---

## 🏁 Getting Started

### Clone the repository

```sh
git clone https://github.com/MatheusSabaudo/Energy-Trading-Pipeline.git
cd Energy-Trading-Pipeline
```

### Start services

```sh
docker compose up --build
```

---

## 📌 Services Access

### Apache Airflow

Access UI at:
`http://localhost:8080`

### PostgreSQL

Internal container service (used by Airflow, pipeline jobs, Metabase)

### pgAdmin – Database Management

Access UI at:
`http://localhost:5050`

**Capabilities:**

* Visual login into PostgreSQL
* Direct SQL querying
* Schema/table inspection
* Manual data validation
* Debugging pipeline outputs

pgAdmin enables **direct interaction with the database layer** without using scripts.

### Metabase – Data Visualization Platform

Access UI at:
`http://localhost:3000`

**Capabilities:**

* Connects directly to PostgreSQL
* Custom dashboards
* Query builder & SQL editor
* API-driven datasets visualization
* Business intelligence layer for energy data

Metabase provides a **full BI layer** for the pipeline, allowing creation of:

* Production dashboards
* Solar performance dashboards
* Economic analysis dashboards
* API-ingested data dashboards
* Trading signal visualization

---

## 📊 Solar & Trading Analyses

The `solar_analysis_data/` directory is intended for:

* Solar production datasets
* Market price data
* Model training data
* Forecasting outputs
* API response datasets

---

## 🛠️ Development

Add new DAGs inside `dags/` and restart Airflow.

---

## 📦 Deployment

Supports staging and production with:

* Secure env configs
* External DB
* Auth-enabled Airflow
* Container orchestration
* BI layer separation (Metabase)
* Admin tooling (pgAdmin)

---

## 📄 License

MIT License --- © 2026 Matheus Sabaudo

---

## 📬 Contributions

Issues and pull requests are welcome.

---
