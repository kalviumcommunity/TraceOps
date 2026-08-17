"""
Unit tests for alert_config module (Assignment 2.56)
"""

import sys
import os
import pytest

# Add root directory to sys.path to allow importing alert_config
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from alert_config import ALERT_THRESHOLDS, check_alerts


def test_alert_thresholds_structure():
    """Task 1: Verify at least three metrics are defined with thresholds, directions, and messages."""
    assert len(ALERT_THRESHOLDS) >= 3
    for key, config in ALERT_THRESHOLDS.items():
        assert "metric" in config
        assert "threshold" in config
        assert "direction" in config
        assert "severity" in config
        assert "message" in config
        assert config["direction"] in ["above", "below"]
        assert config["severity"] in ["critical", "warning"]


def test_check_alerts_churn_breached():
    """Task 2 & 4: Verify churn_rate exceeding threshold triggers critical alert."""
    metrics = {
        "churn_rate": 8.2,
        "avg_order_value": 35.0,
        "null_percentage": 2.0
    }
    alerts = check_alerts(metrics, ALERT_THRESHOLDS)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["key"] == "churn_rate"
    assert alert["metric"] == "Churn Rate"
    assert alert["value"] == 8.2
    assert alert["threshold"] == 7.0
    assert alert["severity"] == "critical"
    assert "Investigate" in alert["message"] or "safe limit" in alert["message"]


def test_check_alerts_aov_breached():
    """Task 2 & 4: Verify avg_order_value dropping below threshold triggers warning alert."""
    metrics = {
        "churn_rate": 5.0,
        "avg_order_value": 25.0,
        "null_percentage": 1.0
    }
    alerts = check_alerts(metrics, ALERT_THRESHOLDS)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["key"] == "avg_order_value"
    assert alert["metric"] == "Avg Order Value"
    assert alert["value"] == 25.0
    assert alert["threshold"] == 30.0
    assert alert["severity"] == "warning"


def test_check_alerts_null_percentage_breached():
    """Task 2 & 4: Verify null_percentage exceeding threshold triggers warning alert."""
    metrics = {
        "churn_rate": 4.0,
        "avg_order_value": 45.0,
        "null_percentage": 6.5
    }
    alerts = check_alerts(metrics, ALERT_THRESHOLDS)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["key"] == "null_percentage"
    assert alert["severity"] == "warning"


def test_check_alerts_no_breach():
    """Verify no alerts trigger when all metrics are within safe boundaries."""
    metrics = {
        "churn_rate": 5.0,        # <= 7.0
        "avg_order_value": 45.0,   # >= 30.0
        "null_percentage": 2.0     # <= 5.0
    }
    alerts = check_alerts(metrics, ALERT_THRESHOLDS)
    assert len(alerts) == 0


def test_config_overrides():
    """Task 3: Verify custom threshold config changes threshold evaluation."""
    custom_config = {
        "churn_rate": {
            "metric": "Churn Rate",
            "threshold": 10.0,  # raised threshold
            "direction": "above",
            "severity": "critical",
            "message": "Custom threshold exceeded."
        }
    }
    metrics = {"churn_rate": 8.5}
    # 8.5 is below 10.0 threshold, so no alert
    alerts = check_alerts(metrics, custom_config)
    assert len(alerts) == 0

    # 11.0 is above 10.0 threshold, so alert triggers
    metrics_high = {"churn_rate": 11.0}
    alerts_high = check_alerts(metrics_high, custom_config)
    assert len(alerts_high) == 1
    assert alerts_high[0]["threshold"] == 10.0
