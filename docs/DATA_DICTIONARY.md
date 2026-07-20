# Data Dictionary

## Dataset Overview

This dataset contains customer transaction records used for revenue, retention, and customer segmentation analysis. It is updated daily from the CRM and sales intake systems.

- Last Updated: 2026-07-20
- Maintained By: Data Engineering Team

## Columns

### customer_id

- Type: Integer
- Business Meaning: Unique customer identifier from CRM system
- Example: 12456
- Null Handling: Never null (primary key)
- Related KPI: Customer tracking, lifetime value calculation
- Updates: Assigned when the customer is created in CRM

### trnx_amt

- Type: Float
- Business Meaning: Revenue from a single transaction
- Example: 150.99
- Unit: USD
- Null Handling: Very rare - investigate if found
- Related KPI: Monthly revenue, average transaction value, customer lifetime value
- Updates: Set when the transaction completes

### purchase_date

- Type: Datetime
- Business Meaning: Date the transaction was completed
- Example: 2025-01-15
- Null Handling: Never null in the trusted data feed
- Related KPI: Sales velocity, monthly revenue trend
- Updates: Recorded at transaction completion time

### cust_segment

- Type: String
- Business Meaning: Customer market segment (B2B/B2C/SMB)
- Valid Values: B2B, B2C, SMB
- Example: B2B
- Null Handling: If null, classify as UNKNOWN
- Related KPI: Segment revenue, segment churn rate
- Updates: Monthly from CRM classification

### flag_churn

- Type: Integer
- Business Meaning: Binary indicator of whether the customer churned within 90 days
- Example: 0
- Null Handling: Nulls should be treated as missing and investigated
- Related KPI: Churn rate prediction, retention analytics
- Updates: Derived after retention window closes

## KPI Mapping

### Monthly Revenue

- Formula: SUM(trnx_amt)
- Related Columns: trnx_amt, purchase_date
- Why It Matters: Tracks total company revenue
- Update Frequency: Daily

### Sales Velocity

- Formula: COUNT(transactions) / days
- Related Columns: purchase_date
- Why It Matters: Measures sales activity rate and momentum
- Update Frequency: Weekly

### Segment Revenue

- Formula: SUM(trnx_amt) grouped by cust_segment
- Related Columns: trnx_amt, cust_segment
- Why It Matters: Identifies which segments drive the most profit
- Update Frequency: Monthly

### Churn Rate

- Formula: SUM(flag_churn) / total_customers
- Related Columns: flag_churn, customer_id
- Why It Matters: Critical retention metric
- Update Frequency: Quarterly

### Customer Lifetime Value

- Formula: SUM(trnx_amt) grouped by customer_id
- Related Columns: customer_id, trnx_amt
- Why It Matters: Prioritizes high-value customers for retention and upsell
- Update Frequency: Daily

## Ambiguous Columns & Resolutions

### Column: flag_churn

- Original Ambiguity: Does it mean currently churned or will churn in future?
- Resolved Meaning: Historical churn indicator for whether a customer churned within 90 days following the transaction
- Business Interpretation: Used as a target variable for retention modeling
- Proposed Rename: has_churned_90d
- Risk If Misunderstood: A model trained on the wrong interpretation would produce unreliable churn predictions

### Column: cust_segment

- Original Ambiguity: Is this market segment, product segment, or geographic region?
- Resolved Meaning: Customer market segment such as B2B, B2C, or SMB
- Business Interpretation: Drives pricing strategy and sales prioritization
- Proposed Rename: market_segment
- Risk If Misunderstood: Revenue analysis by the wrong dimension would distort segment performance

## Column Relationships

### Revenue per Customer

- Definition: SUM(trnx_amt) grouped by customer_id
- How It Matters: Identifies high-value customers for retention focus and upsell opportunities
- Example: Top 10% of customers generate a disproportionate share of revenue
- Related Columns: customer_id, trnx_amt, cust_segment

### Churn by Segment

- Definition: SUM(flag_churn) / total_customers grouped by cust_segment
- How It Matters: Identifies which segments have the highest churn risk requiring intervention
- Example: SMB may show a higher churn rate than B2B
- Related Columns: flag_churn, cust_segment, customer_id

### Revenue Velocity

- Definition: Rolling sum of trnx_amt over 30-day windows
- How It Matters: Tracks sales momentum and growth rate trends
- Example: Monthly revenue velocity trending up 15% quarter-over-quarter
- Related Columns: trnx_amt, purchase_date
