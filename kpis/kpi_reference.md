# KPI Reference Document

This document formally defines the Key Performance Indicators (KPIs) used across the engineering, product, and finance teams to measure business health and operational effectiveness.

---

## 1. Monthly Active Users (MAU)
- **Definition**: Distinct customers with at least one successful transaction in the last 30 days.
- **Formula**:
  $$MAU = \text{COUNT}(\text{DISTINCT } customer\_id) \text{ WHERE } transaction\_date \ge TODAY() - 30\text{ days}$$
- **Data Source**: `kpi_transactions.csv` (columns: `customer_id`, `transaction_date`, `payment_status` = 'Success')
- **Target Range**: 5,000 - 6,000 users
- **Owner**: Product Manager
- **Update Frequency**: Daily
- **Notes**: Operational indicator of active user engagement. Expect mild seasonal contractions during Q4.

---

## 2. Average Revenue per Customer (ARPU / RPC)
- **Definition**: Average accumulated purchase value generated per unique active customer.
- **Formula**:
  $$RPC = \frac{\sum amount}{\text{COUNT}(\text{DISTINCT } customer\_id)}$$
- **Data Source**: `kpi_transactions.csv` (columns: `amount`, `customer_id`, `payment_status` = 'Success')
- **Target Range**: $90 - $110
- **Owner**: Finance Lead
- **Update Frequency**: Monthly
- **Notes**: Measures pricing health and average cart value. Tracks whether customer value is increasing over time.

---

## 3. Customer Churn Rate
- **Definition**: The percentage of customers active in a baseline 30-day period who have no transaction activity in the subsequent 30-day period.
- **Formula**:
  $$Churn\ Rate = \frac{|Active_{P1} \setminus Active_{P2}|}{|Active_{P1}|}$$
  Where $P1 = [T - 60, T - 30)$ and $P2 = [T - 30, T]$.
- **Data Source**: `kpi_transactions.csv` (columns: `customer_id`, `transaction_date`, `payment_status` = 'Success')
- **Target Range**: 0.0% - 5.0%
- **Owner**: Customer Success Lead
- **Update Frequency**: Monthly
- **Notes**: Critical retention metric. Sudden increases point to onboarding drop-offs or product stability issues.

---

## 4. Payment Success Rate
- **Definition**: The proportion of total authorization attempts that complete successfully.
- **Formula**:
  $$Success\ Rate = \frac{\text{COUNT}(attempts \text{ WHERE } status = 'Success')}{\text{COUNT}(total\ attempts)}$$
- **Data Source**: `kpi_transactions.csv` (columns: `payment_status`)
- **Target Range**: 95.0% - 100.0% (0.95 - 1.00)
- **Owner**: Engineering Lead
- **Update Frequency**: Daily / Real-Time
- **Notes**: Infrastructure health metric. Any drop below 95% triggers an immediate alert to investigate payment gateways.

---

## 5. Customer Acquisition Cost (CAC)
- **Definition**: The average marketing spend required to acquire a single new transacting customer during a 30-day window.
- **Formula**:
  $$CAC = \frac{\text{Total Marketing Spend in Last 30 Days}}{\text{Count of New Customers Acquired in Last 30 Days}}$$
  Where a "new customer" is one whose very first transaction occurs in the last 30 days.
- **Data Source**: Marketing cost ledger + `kpi_transactions.csv` (columns: `customer_id`, `transaction_date`)
- **Target Range**: $0 - $50
- **Owner**: Marketing Director
- **Update Frequency**: Monthly
- **Notes**: Combined with LTV to evaluate marketing efficiency (LTV:CAC ratio target is > 3:1).
