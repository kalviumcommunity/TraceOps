"""
Email Delivery Module for TraceOps Analytics
Sends generated reports via email using smtplib with credentials read from environment variables.
Provides non-blocking error handling to ensure application stability.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_report(report_text: str, recipient: str) -> bool:
    """
    Send report via email using smtplib with environment credentials.

    Parameters:
        report_text (str): The structured report content to send.
        recipient (str): Email address of the recipient.

    Returns:
        bool: True if email sent successfully, False otherwise (non-blocking).
    """
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    try:
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
    except (ValueError, TypeError):
        smtp_port = 587

    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PASSWORD")

    if not sender or not password:
        print("Email credentials not configured. Skipping send.")
        return False

    msg = MIMEMultipart()
    msg["Subject"] = "Weekly Analytics Report"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(report_text, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("Send failed: " + str(e))
        return False


def send_report_email(report_text: str, recipient: str) -> bool:
    """Alias for send_report to support send_report_email interface."""
    return send_report(report_text, recipient)
