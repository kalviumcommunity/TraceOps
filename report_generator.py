"""
Report Generator Module for TraceOps Analytics
Generates structured summaries (KPI summary, key finding, recommended action) from DataFrame analysis output.
"""

import datetime
import pandas as pd


def generate_report(df: pd.DataFrame, report_date=None) -> str:
    """
    Generate a structured text report from analysis output.

    Parameters:
        df (pd.DataFrame): Dataframe containing transaction/analytics data.
        report_date (datetime.date or str, optional): Date for the report. Defaults to today's date.

    Returns:
        str: Formatted report text with KPI Summary, Key Finding, and Recommended Action.
    """
    if report_date is None:
        report_date = datetime.date.today()

    if df is None or len(df) == 0:
        revenue = 0.0
        customers = 0
        avg_order = 0.0
        top_segment = "N/A"
    else:
        # Standardize calculation with fallback options for column names
        rev_col = "revenue" if "revenue" in df.columns else ("amount" if "amount" in df.columns else None)
        revenue = float(df[rev_col].sum()) if rev_col else 0.0
        
        cust_col = "customer_id" if "customer_id" in df.columns else None
        customers = int(df[cust_col].nunique()) if cust_col else len(df)
        
        avg_order = float(df[rev_col].mean()) if (rev_col and len(df) > 0) else 0.0
        
        seg_col = "segment" if "segment" in df.columns else ("customer_type" if "customer_type" in df.columns else None)
        if seg_col and rev_col and not df.empty:
            top_segment = str(df.groupby(seg_col)[rev_col].sum().idxmax())
        else:
            top_segment = "N/A"

    lines = []
    lines.append("WEEKLY ANALYTICS REPORT")
    lines.append("Date: " + str(report_date))
    lines.append("")
    lines.append("== KPI SUMMARY ==")
    lines.append(f"Total Revenue: ${revenue:,.0f}")
    lines.append(f"Active Customers: {customers:,}")
    lines.append(f"Average Order: ${avg_order:,.0f}")
    lines.append("")
    lines.append("== KEY FINDING ==")
    lines.append("Top segment: " + str(top_segment))
    lines.append("")
    lines.append("== RECOMMENDED ACTION ==")
    lines.append("Allocate resources to high-growth segments.")

    return "\n".join(lines)
