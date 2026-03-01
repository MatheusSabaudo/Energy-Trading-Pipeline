# dashboard/simple_dashboard.py
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import os
from sqlalchemy import create_engine

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
import userdata_config as cfg

# PostgreSQL connection
engine = create_engine('postgresql+psycopg2://airflow:airflow@localhost:5432/airflow')

def get_recent_data(minutes=30):
    """Get data from last X minutes"""
    query = """
        SELECT 
            timestamp,
            panel_id,
            production_kw,
            temperature_c
        FROM solar_panel_readings
        WHERE timestamp > NOW() - INTERVAL '%(minutes)s minutes'
        ORDER BY timestamp DESC
    """
    return pd.read_sql(query, engine, params={'minutes': minutes})

def get_daily_summary():
    """Get today's summary"""
    query = """
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as readings,
            AVG(production_kw) as avg_production,
            SUM(production_kw) as total_production,
            AVG(temperature_c) as avg_temp
        FROM solar_panel_readings
        WHERE DATE(timestamp) = CURRENT_DATE
        GROUP BY DATE(timestamp)
    """
    return pd.read_sql(query, engine)

def plot_recent_production():
    """Create a simple plot of recent production"""
    df = get_recent_data(30)
    
    if df.empty:
        print("No data in the last 30 minutes")
        return
    
    plt.figure(figsize=(12, 6))
    
    for panel in df['panel_id'].unique():
        panel_data = df[df['panel_id'] == panel]
        plt.plot(panel_data['timestamp'], panel_data['production_kw'],
                marker='o', label=panel, alpha=0.7)
    
    plt.title('Solar Production - Last 30 Minutes')
    plt.xlabel('Time')
    plt.ylabel('Production (kW)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('dashboard/recent_production.png')
    plt.close()
    print("Chart saved to dashboard/recent_production.png")

def print_summary():
    """Print current summary"""
    df = get_recent_data(5)
    daily = get_daily_summary()
    
    print("=" * 60)
    print("SOLAR PRODUCTION DASHBOARD")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not daily.empty:
        print(f"\nTODAY'S SUMMARY:")
        print(f"   Total production: {daily['total_production'].values[0]:.2f} kWh")
        print(f"   Average production: {daily['avg_production'].values[0]:.2f} kW")
        print(f"   Readings: {daily['readings'].values[0]}")
    
    if not df.empty:
        print(f"\nLAST 5 MINUTES:")
        print(f"   Current production: {df['production_kw'].mean():.2f} kW avg")
        print(f"   Active panels: {df['panel_id'].nunique()}")
        print(f"   Temperature: {df['temperature_c'].mean():.1f}°C")
    
    print("\nLATEST READINGS:")
    print(df.head(10).to_string(index=False))

if __name__ == "__main__":
    print_summary()
    plot_recent_production()