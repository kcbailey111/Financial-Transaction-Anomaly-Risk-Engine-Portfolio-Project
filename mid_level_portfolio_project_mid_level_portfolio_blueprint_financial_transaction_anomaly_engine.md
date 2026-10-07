# Flagship Portfolio Project Blueprint: Financial Transaction Anomaly & Risk Engine

## Project Overview
**Target Role:** Mid-Level Data Analyst / Business Intelligence Engineer  
**Core Domain:** Financial Services / Risk & Compliance / Anomaly Detection  
**Primary Tech Stack:** PostgreSQL/SQLite, Python (`pandas`, `SQLAlchemy`), Power BI (DAX, Star Schema), Markdown  

---

## Architecture Pipeline

```text
 ┌────────────────┐       ┌─────────────────┐       ┌──────────────────┐       ┌──────────────────┐
 │  Raw Financial │  SQL  │   Star Schema   │ Power   │  Semantic Model  │ Power BI│ Executive Risk   │
 │  Transactions  │ ─────>│  Data Warehouse │ ──────> │   (Complex DAX)  │ ──────> │   Dashboard &    │
 │  (Messy Data)  │ ETL   │ (Fact & Dims)   │ Query   │  (Anomaly Engine)│ Visuals │   Alert System   │
 └────────────────┘       └─────────────────┘       └──────────────────┘       └──────────────────┘
```

---

## Execution Phases

### Phase 1: Database Engineering & Dimensional Modeling (SQL)
- **Data Ingestion:** Load raw flat financial datasets into a local PostgreSQL/SQLite database inside VSCode.
- **Data Transformation:** Write SQL scripts to normalize transaction dates, parse geographical locations, handle nulls, and clean currency fields.
- **Dimensional Modeling (Star Schema):**
  - `fact_transactions`: `TransactionID`, `Amount`, `MerchantID`, `CustomerID`, `DateKey`, `RiskScore`, `FlagType`
  - `dim_customer`: `CustomerID`, `SignupDate`, `RiskTier`, `AccountBalance`, `CreditScore`
  - `dim_merchant`: `MerchantID`, `Category`, `Location`, `RiskLevel`
  - `dim_date`: `DateKey`, `FullDate`, `Year`, `Quarter`, `Month`, `Day`, `IsWeekend`
- **Advanced Anomaly Queries:**
  - Write SQL window functions (`LAG`, `AVG() OVER()`) to detect rapid transaction frequency or location jumps.
  - Query pattern: Detect "Smurfing/Structuring" (multiple transactions under $10,000 within a 24-hour rolling window).

---

### Phase 2: Python Data Enrichment & Statistical Scoring (VSCode)
- **Script Location:** `src/anomaly_detection.py`
- **Statistical Filtering:**
  - Calculate rolling 30-day customer averages and standard deviations.
  - Flag transactions exceeding 3 standard deviations ($Z > 3$) as statistical outliers.
- **Database Writeback:** Append risk flags and calculated Z-scores directly back to the database target table via `SQLAlchemy`.

---

### Phase 3: Semantic Data Modeling & Advanced DAX (Power BI)
- **Relationships:** Implement a 1-to-Many strict directional Star Schema in Power BI Model View.
- **Key DAX Measures:**
  - **Rolling Volume:** `CALCULATE(SUM(fact_transactions[Amount]), DATESINPERIOD(dim_date[FullDate], MAX(dim_date[FullDate]), -30, DAY))`
  - **YoY Growth:** Time Intelligence calculations comparing current period volume to prior year.
  - **Dynamic Risk Categorization:** Measure-driven categorization for High, Medium, and Low risk thresholds based on dynamic parameter slicers.

---

### Phase 4: Executive Visualizations & Incident Response UI
- **Page 1: Executive Risk Summary**
  - KPI Cards: Total Volume, High-Risk Volume ($), Flagged Transaction Rate (%).
  - Anomaly Heatmaps by Merchant Category and Location.
  - Time-series line chart highlighting dynamic outlier spikes.
- **Page 2: Risk Investigator Drill-Through**
  - Granular customer account lookup.
  - Transaction history detail grid with explicit flag reasons and audit logs.

---

## GitHub Repository Structure

```text
financial-anomaly-engine/
├── data/
│   ├── raw/                # Original source CSVs (Git ignored)
│   └── processed/          # Cleaned, database-ready CSV extracts
├── sql/
│   ├── 01_schema_ddl.sql   # Star schema creation scripts
│   ├── 02_cleaning.sql     # Data sanitization queries
│   └── 03_anomalies.sql    # Complex window functions and detection logic
├── src/
│   └── anomaly_engine.py   # Python statistical outlier detection pipeline
├── dashboards/
│   └── executive_risk.pbix # Power BI report file
├── .gitignore              # Keeps raw data and environment configs private
├── requirements.txt        # Python library dependencies
└── README.md               # Executive Case Study & Project Summary
```

---

## Professional GitHub README Template Structure

1. **Executive Summary:** Define the business problem, total volume analyzed, and key fraud/risk metrics uncovered.
2. **Key Business Insights:** Call out 3 key findings (e.g., *"Merchant Category X saw a 45% spike in micro-transactions matching structuring patterns"*).
3. **Data Architecture Diagram:** Clean visual showing the flow from SQL $\rightarrow$ Python $\rightarrow$ Power BI.
4. **Code Highlights:** Showcase 1–2 well-formatted SQL window functions and 1 complex DAX measure.
5. **Dashboard Screenshots & Interactive Demo:** High-res visuals displaying the report pages and interaction design.