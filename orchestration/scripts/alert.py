#!/usr/bin/env python3
"""
Alert Script for Pipeline Notifications
Sends alerts via email, Slack, or console based on severity
"""

import sys
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import argparse

# Configuration
ALERT_CONFIG = {
    'email': {
        'enabled': True,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender': 'alerts@solardata.com',
        'password': 'your-app-password',  # Use environment variable in production
        'recipients': ['admin@msr.com', 'team@solardata.com']
    },
    'slack': {
        'enabled': False,
        'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    },
    'console': {
        'enabled': True
    }
}

def send_email_alert(subject, message, severity):
    """Send email alert"""
    if not ALERT_CONFIG['email']['enabled']:
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = ALERT_CONFIG['email']['sender']
        msg['To'] = ', '.join(ALERT_CONFIG['email']['recipients'])
        msg['Subject'] = f"[{severity}] {subject}"
        
        # Create HTML email
        html = f"""
        <html>
        <head>
            <style>
                .critical {{ color: red; font-weight: bold; }}
                .warning {{ color: orange; font-weight: bold; }}
                .info {{ color: blue; }}
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #f0f0f0; padding: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2 class="{severity.lower()}">Solar Pipeline Alert - {severity}</h2>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <div class="content">
                <pre>{message}</pre>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        server = smtplib.SMTP(ALERT_CONFIG['email']['smtp_server'], ALERT_CONFIG['email']['smtp_port'])
        server.starttls()
        server.login(ALERT_CONFIG['email']['sender'], ALERT_CONFIG['email']['password'])
        server.send_message(msg)
        server.quit()
        
        print(f"Email alert sent to {len(ALERT_CONFIG['email']['recipients'])} recipients")
        
    except Exception as e:
        print(f"Failed to send email alert: {e}")

def send_slack_alert(subject, message, severity):
    """Send Slack alert via webhook"""
    if not ALERT_CONFIG['slack']['enabled']:
        return
    
    try:
        import requests
        
        color = {
            'CRITICAL': 'danger',
            'WARNING': 'warning',
            'INFO': 'good'
        }.get(severity, 'good')
        
        payload = {
            'attachments': [{
                'color': color,
                'title': f"Solar Pipeline Alert - {severity}",
                'text': message,
                'fields': [
                    {'title': 'Subject', 'value': subject, 'short': True},
                    {'title': 'Time', 'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'short': True}
                ],
                'footer': 'Solar Data Pipeline',
                'ts': int(datetime.now().timestamp())
            }]
        }
        
        response = requests.post(ALERT_CONFIG['slack']['webhook_url'], json=payload)
        if response.status_code == 200:
            print("Slack alert sent")
        else:
            print(f"Slack alert failed: {response.status_code}")
            
    except Exception as e:
        print(f"Failed to send Slack alert: {e}")

def console_alert(subject, message, severity):
    """Print alert to console"""
    if not ALERT_CONFIG['console']['enabled']:
        return
    
    border = "=" * 60
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"\n{border}")
    print(f"ALERT - {severity}")
    print(border)
    print(f"Time: {timestamp}")
    print(f"Subject: {subject}")
    print(f"Message:\n{message}")
    print(border + "\n")

def main():
    parser = argparse.ArgumentParser(description='Send pipeline alerts')
    parser.add_argument('--severity', choices=['INFO', 'WARNING', 'CRITICAL'], default='INFO')
    parser.add_argument('--subject', required=True, help='Alert subject')
    parser.add_argument('--message', required=True, help='Alert message')
    parser.add_argument('--data', help='JSON data with additional context')
    
    args = parser.parse_args()
    
    # Add JSON data if provided
    if args.data:
        try:
            data = json.loads(args.data)
            args.message += f"\n\nAdditional Data:\n{json.dumps(data, indent=2)}"
        except:
            args.message += f"\n\nRaw Data: {args.data}"
    
    # Send alerts through all enabled channels
    console_alert(args.subject, args.message, args.severity)
    send_email_alert(args.subject, args.message, args.severity)
    send_slack_alert(args.subject, args.message, args.severity)
    
    # Exit with appropriate code
    if args.severity == 'CRITICAL':
        sys.exit(2)
    elif args.severity == 'WARNING':
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()