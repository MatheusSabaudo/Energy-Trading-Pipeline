#!/usr/bin/env python3
"""
Anomaly Alert System
Sends alerts for critical anomalies detected in the pipeline
"""

import os
import sys
import argparse
import psycopg2
from datetime import datetime
from pathlib import Path

# Add project root to path for config import
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import userdata_config as cfg

# ============================================================
# CONFIGURATION
# ============================================================
ALERT_CONFIG = {
    'console': {
        'enabled': True
    },
    'thresholds': {
        'critical_anomalies': 1,
        'warning_anomalies': 5,
        'data_delay_hours': 2,
        'quality_threshold': 90
    }
}

# Database connection
DB_CONFIG = cfg.POSTGRES_CONFIG

# ============================================================
# ALERT FUNCTIONS
# ============================================================

def get_active_anomalies():
    """Fetch active anomalies from database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                severity,
                COUNT(*) as count
            FROM gold_anomalies
            WHERE resolution_status = 'Open'
            GROUP BY severity
        """)
        results = cur.fetchall()
        
        critical = 0
        warning = 0
        for severity, count in results:
            if severity == 'Critical':
                critical = count
            elif severity == 'Warning':
                warning = count
        
        cur.close()
        conn.close()
        
        return critical, warning
        
    except Exception as e:
        print(f"Failed to fetch anomalies: {e}")
        return 0, 0

def check_data_freshness():
    """Check if data is arriving on time"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                EXTRACT(EPOCH FROM (NOW() - MAX(timestamp)))/3600 as hours_delayed
            FROM solar_panel_readings
        """)
        hours_delayed = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return hours_delayed or 0
        
    except Exception as e:
        print(f"Failed to check data freshness: {e}")
        return 0

def check_data_quality():
    """Check data quality trends"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                AVG(data_quality_pct) as avg_quality
            FROM gold_daily_panel
            WHERE date >= CURRENT_DATE - 3
        """)
        avg_quality = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return avg_quality or 100
        
    except Exception as e:
        print(f"Failed to check data quality: {e}")
        return 100

def console_alert(message, severity):
    """Print alert to console"""
    border = "=" * 60
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"\n{border}")
    print(f"ALERT - {severity}")
    print(border)
    print(f"Time: {timestamp}")
    print(message)
    print(border + "\n")

def check_and_alert():
    """Main function to check conditions and send alerts"""
    
    # Get data
    critical_count, warning_count = get_active_anomalies()
    hours_delayed = check_data_freshness()
    avg_quality = check_data_quality()
    
    # Determine if we need to alert
    should_alert = False
    alert_reasons = []
    severity = 'INFO'
    
    # Check critical anomalies
    if critical_count >= ALERT_CONFIG['thresholds']['critical_anomalies']:
        should_alert = True
        severity = 'CRITICAL'
        alert_reasons.append(f"{critical_count} critical anomalies")
    
    # Check warning threshold
    if warning_count >= ALERT_CONFIG['thresholds']['warning_anomalies']:
        should_alert = True
        if severity != 'CRITICAL':
            severity = 'WARNING'
        alert_reasons.append(f"{warning_count} warnings")
    
    # Check data delay
    if hours_delayed > ALERT_CONFIG['thresholds']['data_delay_hours']:
        should_alert = True
        if severity != 'CRITICAL':
            severity = 'WARNING'
        alert_reasons.append(f"Data delayed by {hours_delayed:.1f} hours")
    
    # Check data quality
    if avg_quality < ALERT_CONFIG['thresholds']['quality_threshold']:
        should_alert = True
        if severity != 'CRITICAL':
            severity = 'WARNING'
        alert_reasons.append(f"Low data quality: {avg_quality:.1f}%")
    
    # Send alert if needed
    if should_alert:
        message = f"Alert triggered: {', '.join(alert_reasons)}\n"
        message += f"Summary: {critical_count} critical, {warning_count} warnings, "
        message += f"{hours_delayed:.1f}h delay, {avg_quality:.1f}% quality"
        console_alert(message, severity)
        return 2 if severity == 'CRITICAL' else 1
    else:
        message = "No action needed - all systems normal\n"
        message += f"Summary: {critical_count} critical, {warning_count} warnings, "
        message += f"{hours_delayed:.1f}h delay, {avg_quality:.1f}% quality"
        console_alert(message, 'INFO')
        return 0

def main():
    parser = argparse.ArgumentParser(description='Anomaly Alert System')
    parser.add_argument('--force', action='store_true', help='Force alert even if thresholds not met')
    
    args = parser.parse_args()
    
    if args.force:
        console_alert("TEST ALERT - No action required", 'WARNING')
        return 0
    else:
        return check_and_alert()

if __name__ == "__main__":
    sys.exit(main())