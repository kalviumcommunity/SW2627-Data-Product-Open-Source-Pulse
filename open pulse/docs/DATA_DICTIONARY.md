# Data Dictionary

## Dataset Overview

This business-facing schema describes customer transaction records that are updated from the CRM and transaction systems. The current sample uses `transaction_amount` and `transaction_date`; these are the source aliases for `trnx_amt` and `purchase_date` in this dictionary. The current repository does not yet contain source fields for `cust_segment` or `flag_churn`, so those columns are documented as planned enrichment fields.

- **Last Updated**: 2026-08-20
- **Maintained By**: Data Engineering Team
- **Grain**: One transaction for one customer
- **Primary Key**: `customer_id` identifies the customer; a transaction identifier should be added when multiple transactions per customer must be uniquely addressed

## Columns

### `customer_id`

- **Type**: Integer
- **Technical Description**: Unique identifier for a customer in the CRM system
- **Business Meaning**: Links transactions and retention outcomes to the customer account
- **Example**: `12456`
- **Null Handling**: Never null; reject records without an identifier
- **Related KPI**: Customer tracking, customer lifetime value, revenue per customer
- **Updates**: Assigned when a customer is created in the CRM
- **Notes**: Primary business key. The current sample already uses this column.

### `trnx_amt`

- **Type**: Float
- **Technical Description**: Monetary value of a single transaction
- **Business Meaning**: Revenue collected from the customer for that transaction
- **Example**: `150.99`
- **Unit**: USD
- **Null Handling**: Investigate missing values; negative values require business review
- **Related KPI**: Monthly revenue, average transaction value, customer lifetime value
- **Updates**: Set when a transaction completes
- **Notes**: The current sample calls this field `transaction_amount`.

### `purchase_date`

- **Type**: Datetime
- **Technical Description**: UTC date and time at which the transaction occurred
- **Business Meaning**: Establishes the time of sale for revenue and velocity reporting
- **Example**: `2025-01-15`
- **Null Handling**: Never null for completed transactions; reject or quarantine records without a date
- **Related KPI**: Sales velocity, monthly revenue, revenue growth
- **Updates**: Recorded when the transaction completes
- **Notes**: The current sample calls this field `transaction_date`. Normalize it to UTC before aggregation.

### `cust_segment`

- **Type**: String
- **Technical Description**: Customer market-segment classification
- **Business Meaning**: Identifies the customer group used for pricing, sales, and service decisions
- **Valid Values**: `B2B`, `B2C`, `SMB`, `UNKNOWN`
- **Example**: `B2B`
- **Null Handling**: Replace null with `UNKNOWN` and monitor the null rate
- **Related KPI**: Segment revenue, segment profitability, segment churn rate
- **Updates**: Refreshed monthly from CRM classification
- **Notes**: This field is not present in the current repository sample and must be supplied by CRM enrichment.

### `flag_churn`

- **Type**: Integer
- **Technical Description**: Binary indicator that a customer churned within 90 days after the reference transaction
- **Business Meaning**: Historical retention outcome used to calculate churn and train predictive models
- **Valid Values**: `0` = did not churn within 90 days; `1` = churned within 90 days
- **Example**: `0`
- **Null Handling**: Leave unknown until the observation window closes; do not treat an unobserved outcome as `0`
- **Related KPI**: Churn rate, retention rate, retention-model performance
- **Updates**: Populated after the 90-day observation window
- **Notes**: This field is not present in the current repository sample. Keep the outcome window separate from the transaction date to avoid target leakage.

## Column to KPI Mapping

### Monthly Revenue

- **Formula**: `SUM(trnx_amt)` grouped by calendar month of `purchase_date`
- **Related Columns**: `trnx_amt`, `purchase_date`
- **Why It Matters**: Tracks total company revenue and month-over-month growth
- **Update Frequency**: Daily

### Sales Velocity

- **Formula**: `COUNT(transactions) / number_of_days` over a reporting window
- **Related Columns**: `purchase_date` and a transaction identifier
- **Why It Matters**: Measures sales activity rate and momentum
- **Update Frequency**: Weekly

### Segment Revenue

- **Formula**: `SUM(trnx_amt)` grouped by `cust_segment`
- **Related Columns**: `trnx_amt`, `cust_segment`, `purchase_date`
- **Why It Matters**: Identifies the most profitable market segments
- **Update Frequency**: Monthly

### Churn Rate

- **Formula**: `SUM(flag_churn) / COUNT(DISTINCT customer_id)` for customers with a completed 90-day observation window
- **Related Columns**: `flag_churn`, `customer_id`
- **Why It Matters**: Provides the core measure of retention risk
- **Update Frequency**: Quarterly

### Revenue per Customer

- **Formula**: `SUM(trnx_amt) / COUNT(DISTINCT customer_id)` over a defined period
- **Related Columns**: `customer_id`, `trnx_amt`, `purchase_date`, `cust_segment`
- **Why It Matters**: Shows customer value and supports segment-level commercial decisions
- **Update Frequency**: Monthly

## Ambiguous Columns & Resolutions

### `flag_churn`

- **Original Ambiguity**: It is unclear whether the flag means currently churned, previously churned, or likely to churn in the future.
- **Resolved Meaning**: Binary indicator of whether the customer churned within 90 days following the reference transaction.
- **Business Interpretation**: Historical outcome for retention reporting and predictive-model training.
- **Proposed Rename**: `has_churned_90d`
- **Risk If Misunderstood**: A model trained against the wrong time window produces unreliable predictions and may leak future information.

### `cust_segment`

- **Original Ambiguity**: The abbreviation does not state whether the segment is based on the customer, market, product, or geography.
- **Resolved Meaning**: Customer market segment with values `B2B`, `B2C`, or `SMB`.
- **Business Interpretation**: Determines the appropriate pricing, sales, and customer-success approach.
- **Proposed Rename**: `customer_market_segment`
- **Risk If Misunderstood**: Revenue and churn analysis can be grouped by the wrong dimension and lead to incorrect commercial decisions.

### `trnx_amt`

- **Original Ambiguity**: The abbreviation does not specify whether the value is gross, net, refunded, or in which currency.
- **Resolved Meaning**: Net revenue collected for one transaction, expressed in USD.
- **Business Interpretation**: Monetary basis for revenue and customer-value metrics.
- **Proposed Rename**: `transaction_amount_usd`
- **Risk If Misunderstood**: Mixing currencies or gross and net amounts distorts revenue reporting.

## Column Relationships

### Revenue per Customer

- **Definition**: `SUM(trnx_amt)` grouped by `customer_id`
- **How It Matters**: Identifies high-value customers for retention focus and upsell opportunities
- **Example**: The top 10% of customers may generate 50% of revenue
- **Related Columns**: `customer_id`, `trnx_amt`, `purchase_date`

### Churn by Segment

- **Definition**: `SUM(flag_churn) / COUNT(DISTINCT customer_id)` grouped by `cust_segment`, using customers whose 90-day observation window is complete
- **How It Matters**: Identifies segments with the highest retention risk and helps prioritize interventions
- **Example**: SMB customers may show 25% churn compared with 10% for B2B customers
- **Related Columns**: `flag_churn`, `cust_segment`, `customer_id`

### Revenue Velocity

- **Definition**: Rolling 30-day sum of `trnx_amt` ordered by `purchase_date`
- **How It Matters**: Tracks sales momentum and reveals growth or decline before monthly totals are finalized
- **Example**: Revenue velocity can trend 15% higher quarter over quarter even when customer count is flat
- **Related Columns**: `trnx_amt`, `purchase_date`, `customer_id`