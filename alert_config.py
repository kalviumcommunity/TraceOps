"""
Alert Configuration and Threshold Monitoring for TraceOps KPI Dashboard.

This module defines configuration thresholds for operational business metrics
and provides functions to evaluate metrics against limits to surface visual warnings.
"""

ALERT_THRESHOLDS = {
    "churn_rate": {
        "metric": "Churn Rate",
        "threshold": 7.0,
        "direction": "above",  # alert when value is above threshold
        "severity": "critical",
        "message": "Churn exceeds safe limit. Investigate retention."
    },
    "avg_order_value": {
        "metric": "Avg Order Value",
        "threshold": 30.0,
        "direction": "below",  # alert when value drops below threshold
        "severity": "warning",
        "message": "AOV below target. Check pricing and product mix."
    },
    "null_percentage": {
        "metric": "Data Quality",
        "threshold": 5.0,
        "direction": "above",  # alert when null % is above threshold
        "severity": "warning",
        "message": "Null percentage too high. Check data pipeline."
    }
}


def check_alerts(metrics_dict, thresholds=None):
    """Check computed metrics against defined thresholds.

    Args:
        metrics_dict (dict): Dictionary mapping metric keys to current numeric values.
        thresholds (dict, optional): Dictionary of threshold configurations.
            Defaults to ALERT_THRESHOLDS.

    Returns:
        list: List of triggered alert dictionaries containing:
            key, metric, value, threshold, severity, and message.
    """
    if thresholds is None:
        thresholds = ALERT_THRESHOLDS

    triggered = []
    for key, config in thresholds.items():
        if key not in metrics_dict:
            continue
        value = metrics_dict[key]
        threshold = config["threshold"]

        if config["direction"] == "above" and value > threshold:
            triggered.append({
                "key": key,
                "metric": config["metric"],
                "value": value,
                "threshold": threshold,
                "severity": config["severity"],
                "message": config["message"]
            })
        elif config["direction"] == "below" and value < threshold:
            triggered.append({
                "key": key,
                "metric": config["metric"],
                "value": value,
                "threshold": threshold,
                "severity": config["severity"],
                "message": config["message"]
            })
    return triggered
