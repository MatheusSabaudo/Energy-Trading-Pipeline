# 📈 Energy Trading Pipeline

A modular **data ingestion & processing pipeline** designed to support energy trading analysis and forecasting workflows.
This repository combines **workflow orchestration (Airflow)**, **database support (PostgreSQL)**, and **data analysis for solar and trading signals** into a containerized environment.

---

## 🧠 Project Overview

The **Energy Trading Pipeline** provides a structured ecosystem to:

* Automate data ingestion from energy sources (e.g., solar production, market feeds)
* Store and manage time‑series energy data using PostgreSQL
* Orchestrate repeatable workflows using **Apache Airflow**
* Generate analysis datasets for downstream trading models or dashboards

---

## 🚀 Features
```
✅ Airflow‑based orchestration
✅ PostgreSQL integration
✅ Solar data analysis pipeline
✅ Containerized deployment
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

## 🧪 Prerequisites

* Docker\
* Docker Compose\
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

## 📌 Airflow

Access UI at:
`http://localhost:8080`

---

## 📊 Solar & Trading Analyses

The `solar_analysis_data/` directory is intended for:

* Solar production datasets\
* Market price data\
* Model training data\
* Forecasting outputs

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

---

## 📄 License

MIT License --- © 2026 Matheus Sabaudo

---

## 📬 Contributions

Issues and pull requests are welcome.

---

# 📘 PROJECT STRUCTURE & ANALYSIS ROADMAP

This repository is designed to **simulate, analyze, and optimize solar energy production** and its economic impact. The workflow is divided into three main phases: **Meteorology (Q1), Production (Q2), and Economic Analysis (Q3)**.

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

**Step-by-step:**

1. **Temperature:** compute average, max, min; affects panel efficiency (loss above 25°C).
2. **Cloud Cover:** average, max, min, std, median; categorize as Clear (<20%), Partly Cloudy (20–60%), Cloudy (>60%). Provides the **cloud factor** for production.
3. **UV Index:** average, max, min, std, median; categorize Low (<2), Moderate (2–5), High (>5); correlates to irradiance intensity.
4. **Wind Speed:** average, max, min, std, median; categorize Calm (<5), Light (5–20), Moderate (20–40), Strong (≥40); affects cooling, panel efficiency, and design load.
5. **Solar Angle:** compute daily average, max, min, peak hours.
6. **Solar Potential:** average, max, min, std, median; used for energy output; zero-production periods identified.
7. **Worst-Case Scenario:** select worst historical days to model **battery sizing** and resilience.

**Outcome:** Q1 converts raw weather data into **solar exposure metrics and environmental risk factors**.

---

## Step 2 – Q2: Production Modeling

**Goal:** Convert Q1 metrics into **hourly, daily, and monthly kWh production**.

**Step-by-step:**

1. **Cloud Factor:** scale production 0.1 → 1 depending on cloudiness.
2. **Temperature Loss:** apply efficiency loss above 25°C (temperature coefficient).
3. **UV Factor:** scale production based on solar irradiance.
4. **Production Factor:**

```
production_factor = solar_factor × cloud_factor × temp_efficiency × uv_factor × derating_factor
```
Includes real-world derating.

5. **Hourly kWh Calculation:**

```
hourly_kWh = production_factor × panel_power × panel_efficiency - system_losses
```
System losses include soiling, degradation, availability, inverter losses.

6. **Daily Aggregation:** sum hourly kWh per day.
7. **Monthly Aggregation:** sum daily kWh per month.
8. **Annual Production:** sum monthly kWh (planned).

**Outcome:** Q2 produces realistic energy output estimates considering environmental factors, panel specs, and system losses.

---

## Step 3 – Q3: Economic & Financial Analysis

**Goal:** Translate energy production into **financial metrics**.

**Step-by-step:**

1. **Economic Parameters:** panel power, installation cost, annual maintenance, electricity rate, sell-back rate, incentives, household consumption.
2. **Self-Consumption Analysis:**

   * Evaluate energy consumed vs sold to grid.
   * Compute savings (`self_consumed × electricity rate`)
   * Compute revenue (`grid_injected × sell-back rate`)
   * Compute incentives (e.g., Scambio sul posto).
3. **Optimal Scenario Selection:** test different consumption ratios (20–70%) → select scenario with lowest payback.
4. **Long-Term Cash Flow:** apply seasonal adjustments → estimate annual production, lifetime savings, ROI, payback, and total net profit.
5. **Solar vs Grid Comparison:** compare cost of electricity from grid vs solar → calculate 20-year savings and break-even electricity rate.

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

**Key Principles:**

1. **Data-driven:** Meteorological data drives production estimates.
2. **Physics-based modeling:** Panel efficiency and environmental factors simulate realistic output.
3. **Financial modeling:** Converts kWh into savings, revenue, and ROI.
4. **Resilience planning:** Worst-case scenario informs battery sizing.
5. **Scenario flexibility:** Supports multiple panel types, consumption strategies, and financial assumptions.

**Result:** The pipeline provides **reliable, actionable insights** for solar energy production, financial return, and investment optimization.

---

## 🌐 Future Work – Interactive Website Dashboard

Future extension: create a **web-based dashboard hosted on GitHub Pages** to visualize all pipeline outputs.

**Key Features:**

* Overview dashboard: daily, monthly, and annual production; self-consumption vs grid injection; total savings and revenue.
* Technical Sheet (Scheda Tecnica): display meteorological metrics, panel specs, hourly/daily/monthly kWh, worst-case analysis, and battery sizing.
* Interactive graphs: line charts, bar charts, pie charts, heatmaps for trends.
* Scenario testing interface: adjust panel type, self-consumption ratio, or derating factor and update production/financial metrics in real time.
* Implementation: use static site generators or JavaScript libraries (Plotly.js, D3.js, or Streamlit deployed as static pages); data from `solar_analysis_data/` in JSON/CSV.

**Benefit:** Users can explore energy production, financial scenarios, and technical calculations **without running Python scripts locally**.
