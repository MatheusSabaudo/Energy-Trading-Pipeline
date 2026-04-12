#!/usr/bin/env python3
"""
Alert Script for Pipeline Notifications
Sends alerts via email, Slack, or console based on severity
"""

import argparse
import json
import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ALERT_CONFIG = {
    'email': {
        'enabled': True,
        'smtp_server': os.getenv('ALERT_SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('ALERT_SMTP_PORT', '587')),
        'sender': os.getenv('ALERT_SENDER', 'alerts@solardata.com'),
        'password': os.getenv('ALERT_PASSWORD', ''),
        'recipients': [
            recipient.strip()
            for recipient in os.getenv('ALERT_RECIPIENTS', 'admin@msr.com').split(',')
            if recipient.strip()
        ],
    },
    'slack': {
        'enabled': os.getenv('ALERT_SLACK_ENABLED', 'false').lower() == 'true',
        'webhook_url': os.getenv('ALERT_SLACK_WEBHOOK_URL', ''),
    },
    'console': {
        'enabled': True,
    },
}


def send_email_alert(subject, message, severity):
    if not ALERT_CONFIG['email']['enabled']:
        return
    if not ALERT_CONFIG['email']['password']:
        print("Email alert skipped: ALERT_PASSWORD is not configured")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = ALERT_CONFIG['email']['sender']
        msg['To'] = ', '.join(ALERT_CONFIG['email']['recipients'])
        msg['Subject'] = f"[{severity}] {subject}"

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

    except Exception as exc:
        print(f"Failed to send email alert: {exc}")


def send_slack_alert(subject, message, severity):
    if not ALERT_CONFIG['slack']['enabled']:
        return
    if not ALERT_CONFIG['slack']['webhook_url']:
        print("Slack alert skipped: ALERT_SLACK_WEBHOOK_URL is not configured")
        return

    try:
        import requests

        color = {
            'CRITICAL': 'danger',
            'WARNING': 'warning',
            'INFO': 'good',
        }.get(severity, 'good')

        payload = {
            'attachments': [{
                'color': color,
                'title': f"Solar Pipeline Alert - {severity}",
                'text': message,
                'fields': [
                    {'title': 'Subject', 'value': subject, 'short': True},
                    {'title': 'Time', 'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'short': True},
                ],
                'footer': 'Solar Data Pipeline',
                'ts': int(datetime.now().timestamp()),
            }]
        }

        response = requests.post(ALERT_CONFIG['slack']['webhook_url'], json=payload, timeout=15)
        if response.status_code == 200:
            print("Slack alert sent")
        else:
            print(f"Slack alert failed: {response.status_code}")

    except Exception as exc:
        print(f"Failed to send Slack alert: {exc}")


def console_alert(subject, message, severity):
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

    if args.data:
        try:
            data = json.loads(args.data)
            args.message += f"\n\nAdditional Data:\n{json.dumps(data, indent=2)}"
        except Exception:
            args.message += f"\n\nRaw Data: {args.data}"

    console_alert(args.subject, args.message, args.severity)
    send_email_alert(args.subject, args.message, args.severity)
    send_slack_alert(args.subject, args.message, args.severity)

    if args.severity == 'CRITICAL':
        sys.exit(2)
    if args.severity == 'WARNING':
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
