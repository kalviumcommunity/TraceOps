-- ==============================================================================
-- Query 1: Refactored - Explicit Column Selection (Eliminating SELECT *)
-- ==============================================================================
-- Business Question: What are the transactions and customer profiles for 2024?
-- Performance Improvement: Avoids retrieving unnecessary metadata columns,
-- reducing network transfer, I/O, and memory footprint.
-- ==============================================================================

SELECT 
    t.transaction_id,    -- Unique transaction ID: Required for row identification & primary key tracking
    t.transaction_date,  -- Transaction timestamp: Required for time-series trend analysis & 2024 filtering
    t.amount,            -- Transaction amount: Required for financial metrics & revenue aggregations
    t.customer_id,       -- Customer FK: Required for joining with customer dimension & entity resolution
    c.customer_name,     -- Customer name: Required for business presentation & report displays
    c.country,           -- Country location: Required for regional performance & geographic segmentation
    c.account_type       -- Account classification: Required for tier/cohort analysis (e.g., Enterprise/SMB)
FROM transactions t
JOIN customers c ON t.customer_id = c.id
WHERE t.transaction_date >= '2024-01-01' AND t.transaction_date <= '2024-12-31'
LIMIT 1000;
