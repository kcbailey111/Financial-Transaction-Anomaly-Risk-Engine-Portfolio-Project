# Portfolio Learning Roadmap: Data Analyst and Business Intelligence

You already have the part most portfolios skip: a real load into a warehouse. `src/ingest_data.py` reads a raw CSV, cleans column names, writes `raw_transactions` in `data/financial_warehouse.db`, and checks the row count. The SQL model, the business questions, the dashboard, and the write-up are still ahead of you. Those are the pieces that map to a data analyst or business intelligence job.

Hiring managers for those roles want to see that you can take messy data, model it so it can be queried reliably, answer a business question with SQL, and explain the result to someone who does not write code. Anomaly detection is a good theme. The skill that gets you hired is the path from raw rows to a decision someone could act on.

## 1. Start with a stakeholder and three questions

Before more code, write one paragraph in the README: who uses this, and what decision it supports. Something like a fraud or compliance analyst who has to decide which customers or merchants to review this week.

Then lock three questions you will answer with numbers. For this dataset, useful ones are:

- Which customers show bursts of activity that look like structuring (many payments just under a reporting threshold in a short window)?
- Which merchant categories concentrate high-risk volume, and is that a few customers or a broad pattern?
- How does flagged volume this month compare with the same month last year, and with each customer’s own recent baseline?

Every table, measure, and chart after this should serve one of those questions. If it does not, it is extra.

## 2. Audit the raw table before you model it

Build `sql/01_eda.sql` against `raw_transactions`. This is the skill you will use on day one of a job: you do not trust a source until you have measured it.

Check:

- Row count, distinct customers, distinct merchants, date min and max
- Nulls and blanks on amount, customer id, merchant, and date
- Duplicate transaction ids
- Amounts that are zero, negative, or absurdly large
- How many rows would fail a join if customer or merchant is missing

Write the findings in plain language: “12% of rows have a null merchant; I excluded them from the fact table and counted them in a data-quality measure.” That sentence is more impressive in an interview than a perfect schema with no caveats.

## 3. Build a star schema you can defend

This is the core BI skill in the blueprint. Create `sql/02_star_schema.sql` with:

- `dim_customer`, `dim_merchant`, `dim_date`
- `fact_transactions` at one row per transaction

Practice saying the grain out loud: “one row in the fact table is one transaction.” Then name the foreign keys and what would break if you put merchant category on the fact instead of on `dim_merchant` (you would repeat text, and a category rename would require updating every historical row).

Populate dimensions with `INSERT … SELECT DISTINCT`, then load the fact table by joining back to the surrogate or natural keys. After the load, assert that fact row count plus rejected rows equals the staging count. Analysts who can prove a model did not drop data stand out.

Keep SQLite for the portfolio. The window functions and star schema transfer to PostgreSQL and to warehouse SQL. You do not need a second database engine to learn the job.

## 4. Answer the questions in SQL, then add the statistics

`sql/03_analytics.sql` should come before `src/anomaly_engine.py`. SQL is what analyst interviews test. Python scoring is a bonus.

Work through these in order, and be able to explain each one without reading the script:

- Customer spend rank with `DENSE_RANK()`
- A customer’s prior transaction with `LAG()`, so you can see time and amount jumps
- A 7-day or 30-day rolling average with a window frame
- Structuring: count of transactions under a threshold inside a 24-hour window
- Outliers versus that customer’s own history (average and standard deviation), because a $5,000 charge is normal for one customer and extreme for another

SQLite has no `STDDEV()`. You will compute variance from `AVG(x * x) - AVG(x) * AVG(x)` inside the window, then take the square root in SQL or in Python. Working that out yourself is the lesson.

Use Python only for the piece SQL is clumsy at: rolling 30-day mean and standard deviation per customer, a z-score, and a flag written back to the fact table with SQLAlchemy. Keep the rules in one place and document the threshold (for example, z greater than 3). Arbitrary cutoffs are fine if you can say why you chose them and how a reviewer would change them.

## 5. Learn one BI tool deeply

Power BI is the right primary tool for this blueprint: star schema, relationships, and DAX are exactly what BI interviews ask about. Tableau is worth a second pass later if a job posting requires it. Shipping two thin dashboards teaches less than one report you can demo live.

In Power BI:

- Import the star schema and set one-to-many relationships from dimensions to `fact_transactions`, single direction.
- Hide raw id columns and put measures in a measure table.
- Build the measures in the blueprint: 30-day rolling volume, year-over-year volume, and a risk band driven by a what-if parameter.
- Two pages only. Page one is the executive view: total volume, high-risk dollars, flagged rate, a trend with spikes called out, and a heatmap by category or location. Page two is the investigator view: pick a customer, see their history, and read why each row was flagged.

For each visual, write the sentence it supports. “Card spend in travel jumped 40% and three customers account for most of the new flags” is a BI deliverable. A chart with no sentence is a screenshot.

## 6. Package it the way a recruiter will actually read it

Replace the one-line README with a one-page case study:

- Problem, data volume, and the decision the dashboard supports
- Three findings with a number in each
- The architecture diagram you already sketched: raw CSV, SQLite star schema, Python scores, Power BI
- One SQL window query and one DAX measure, short enough to read
- Two dashboard screenshots and a 60-second description of a click path: filter to a category, drill to a customer, read the flag reason

On a resume, one line should carry a metric from your own results, once you have them. “Modeled 200k card transactions into a star schema and flagged structuring and statistical outliers for investigator review” is stronger than a tool list.

Put `financial_warehouse.db` and the raw CSV in `.gitignore` if they are large, and keep the SQL and Python as the source of truth so someone else can rebuild the warehouse.

## How to study this so it sticks

Do the SQL yourself in small steps. After each script, explain it back in your own words: grain, join keys, what the window is partitioned by, and which rows the filter removes. That is the same explanation you will give in an interview when someone says “walk me through this project.”

A practical order for the next few weeks:

1. Business questions and an EDA script
2. Star schema plus a reconciliation query
3. Analytics SQL for the three questions
4. Python z-scores written back to the fact table
5. Power BI model and two pages
6. README case study and resume bullet

Phase 1 is the highest-leverage next step. Start `sql/01_eda.sql` with four checks: row count, distinct customers and merchants, date range, and null rates on amount, customer, merchant, and date. Interpret the data quality before you design the tables.
