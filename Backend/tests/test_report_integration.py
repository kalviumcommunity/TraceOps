"""
Unit Tests for Insight Sharing & Email Report Integration
Tests report generation, email sending with smtplib, non-blocking error handling, and credential management.
"""

import os
import sys
import datetime
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

# Add parent directory to sys.path to import root modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from report_generator import generate_report
from email_sender import send_report, send_report_email


@pytest.fixture
def sample_df():
    """Returns a sample DataFrame for testing report generation."""
    return pd.DataFrame({
        "transaction_id": ["TX1", "TX2", "TX3", "TX4", "TX5"],
        "customer_id": ["C1", "C2", "C1", "C3", "C2"],
        "revenue": [100.0, 200.0, 150.0, 300.0, 250.0],
        "segment": ["Enterprise", "SMB", "Enterprise", "Startup", "SMB"]
    })


def test_generate_report_sections(sample_df):
    """Test Task 1 & Task 3: generate_report includes KPI summary, key finding, and recommendation."""
    report_date = "2026-08-17"
    report = generate_report(sample_df, report_date)

    assert "WEEKLY ANALYTICS REPORT" in report
    assert f"Date: {report_date}" in report
    assert "== KPI SUMMARY ==" in report
    assert "== KEY FINDING ==" in report
    assert "== RECOMMENDED ACTION ==" in report

    # Verify real computed values
    total_rev = sample_df["revenue"].sum()
    active_cust = sample_df["customer_id"].nunique()
    avg_order = sample_df["revenue"].mean()
    top_seg = sample_df.groupby("segment")["revenue"].sum().idxmax()  # SMB has 450 total

    assert f"Total Revenue: ${total_rev:,.0f}" in report
    assert f"Active Customers: {active_cust:,}" in report
    assert f"Average Order: ${avg_order:,.0f}" in report
    assert f"Top segment: {top_seg}" in report
    assert "Allocate resources" in report or "Review segment performance" in report


def test_generate_report_empty_df():
    """Test generate_report with empty DataFrame."""
    empty_df = pd.DataFrame(columns=["revenue", "customer_id", "segment"])
    report = generate_report(empty_df, "2026-08-17")
    assert "== KPI SUMMARY ==" in report
    assert "== KEY FINDING ==" in report
    assert "== RECOMMENDED ACTION ==" in report


def test_send_report_unconfigured_credentials(monkeypatch):
    """Test Task 2 & Task 5: send_report returns False when credentials are missing from env."""
    monkeypatch.delenv("SENDER_EMAIL", raising=False)
    monkeypatch.delenv("SENDER_PASSWORD", raising=False)

    success = send_report("Report text", "test@example.com")
    assert success is False

    success_alias = send_report_email("Report text", "test@example.com")
    assert success_alias is False


def test_send_report_non_blocking_error_handling(monkeypatch):
    """Test Task 4: send_report logs error and returns False without crashing when SMTP fails."""
    monkeypatch.setenv("SENDER_EMAIL", "sender@example.com")
    monkeypatch.setenv("SENDER_PASSWORD", "secret123")
    monkeypatch.setenv("SMTP_SERVER", "smtp.invalid.domain")
    monkeypatch.setenv("SMTP_PORT", "587")

    with patch("smtplib.SMTP", side_effect=Exception("Connection timed out")):
        success = send_report("Report text", "recipient@example.com")
        assert success is False


def test_send_report_success(monkeypatch):
    """Test Task 2: Successful email delivery via smtplib."""
    monkeypatch.setenv("SENDER_EMAIL", "sender@example.com")
    monkeypatch.setenv("SENDER_PASSWORD", "secret123")
    monkeypatch.setenv("SMTP_SERVER", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")

    mock_smtp_instance = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp_instance) as mock_smtp_class:
        success = send_report("Report text", "recipient@example.com")
        assert success is True
        mock_smtp_class.assert_called_once_with("smtp.example.com", 587)
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("sender@example.com", "secret123")
        mock_smtp_instance.send_message.assert_called_once()
        mock_smtp_instance.quit.assert_called_once()


def test_env_example_file_structure():
    """Test Task 5: Verify .env.example contains required SMTP env var templates."""
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env.example"))
    assert os.path.exists(env_path)

    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "SENDER_EMAIL=" in content
    assert "SENDER_PASSWORD=" in content
    assert "SMTP_SERVER=" in content
    assert "SMTP_PORT=" in content
