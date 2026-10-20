# Financial Transaction Anomaly and Risk Engine

Portfolio project for data analyst and business intelligence roles in financial services.

The deliverable is a warehouse a risk reviewer can trust: cleaned source data, a star schema, SQL and Python risk flags, and a Power BI report that shows **who to review and why**.

| | |
| --- | --- |
| **Status** | Ingestion works. The star schema, anomaly rules, and dashboard are not built yet. |
| **Stack** | SQLite, Python (`pandas`, SQLAlchemy), SQL, Power BI |
| **Data loaded** | 6,146 cards in `raw_transactions` |
| **Schema design** | [docs/star_schema.md](docs/star_schema.md) |

Findings will be added after the analysis exists. This README describes the decision the project supports and the data that is actually loaded.

---

## Business problem

A fraud or compliance analyst has a queue of accounts and must decide which customers or merchants to review this week.

The engine ranks that queue with three questions:

1. **Structuring.** Which customers show bursts of payments just under a reporting threshold in a short window?
2. **Concentration.** Which merchant categories hold most of the high-risk volume, and is that a few customers or a broad pattern?
3. **Baseline.** How does flagged volume this month compare with the same month last year, and with each customer's own recent history?

Every table, measure, and chart should serve one of those questions.

---

## Data loaded today

`src/ingest_data.py` reads `data/raw/cards_data.csv`, standardizes column names, and writes a SQLite staging table.

| Item | Value |
| --- | --- |
| Database | `data/financial_warehouse.db` |
| Staging table | `raw_transactions` |
| Rows | 6,146 |
| Grain | One row per **card**, not one row per purchase |

This file is **card master data**: client, brand, card type, credit limit, open date, chip flag, and a dark-web flag.

It does **not** contain purchase amount, merchant, or transaction time. The table name `raw_transactions` is ahead of the data. Until a transactions file is loaded, there is no fact table to analyze.

**Will feed `dim_card`:** `id`, `client_id`, `card_brand`, `card_type`, `has_chip`, `num_cards_issued`, `credit_limit`, `acct_open_date`, `year_pin_last_changed`, `card_on_dark_web`

**Stay out of the model and the dashboard:** `card_number`, `cvv`

Raw CSVs are gitignored.

---

## Architecture

```text
cards_data.csv                 loaded
        |
        |  Python (pandas, SQLAlchemy)
        v
raw_transactions               loaded (one row per card)
        |
        |  SQL cleaning + star-schema load     planned
        v
dim_card / dim_client / dim_date / dim_merchant
fact_transactions              needs a transactions source
        |
        |  SQL windows + Python z-scores       planned
        v
Risk flags written back to the fact table
        |
        |  Power BI relationships + DAX        planned
        v
Executive risk page + investigator drill-through
```

The target model, including what a star schema is, is in [docs/star_schema.md](docs/star_schema.md).

---

## Repository

```text
data/
  raw/                      source CSVs (gitignored)
  processed/                cleaned extracts (planned)
  financial_warehouse.db    SQLite warehouse
src/
  ingest_data.py            CSV -> staging table
  transform.py              dimensional load (planned)
  anomaly_engine.py         z-score writeback (planned)
sql/                        EDA, DDL, anomaly queries (planned)
dashboards/                 Power BI report (planned)
docs/
  star_schema.md            star schema explainer and target model
```

---

## Setup

Python 3, plus the packages in `requirements.txt`. From the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/ingest_data.py
```

Command Prompt: `.venv\Scripts\activate.bat` instead of `Activate.ps1`.

The script checks that the CSV exists, replaces `raw_transactions`, and compares the database row count to the file. A passing run prints `INTEGRITY CHECK PASSED`.

Use `.venv` so the environment matches `.gitignore`.

---

## Build order

1. Profile `raw_transactions` in `sql/01_eda.sql` (counts, nulls, duplicate card ids, credit limits stored as text).
2. Load a transactions source, then build the star schema in `sql/02_star_schema.sql`. Card rows become `dim_card`.
3. Answer the three business questions in `sql/03_analytics.sql` (ranking, `LAG`, rolling windows, structuring rule).
4. Write customer-level z-scores back to the fact table from `src/anomaly_engine.py`.
5. Model the star schema in Power BI. Two pages: executive risk summary, then customer drill-through with flag reasons.

---

## Key findings

*Placeholder until the analysis is done.*

Each finding will be one sentence with a number, the population it describes, and the action a reviewer would take.

Example of the shape, not a result from this data: "Travel merchants account for 40% of flagged dollars, and three customers drive most of that total."
