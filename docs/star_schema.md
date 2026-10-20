# Star Schema for the Risk Engine

What a star schema is, why analysts use one, and how this project maps onto it.

The design matches the data on disk today and the transaction model still to be built. See the [README](../README.md) for project status and how to run ingestion.

**Contents**

1. [What a star schema is](#1-what-a-star-schema-is)
2. [Why analysts and BI tools use it](#2-why-analysts-and-bi-tools-use-it)
3. [Terms](#3-terms)
4. [Grain comes first](#4-grain-comes-first)
5. [What the warehouse holds today](#5-what-the-warehouse-holds-today)
6. [Target model](#6-target-model)
7. [Load order](#7-load-order)
8. [Power BI relationships](#8-power-bi-relationships)
9. [How the three questions use this schema](#9-how-the-three-questions-use-this-schema)
10. [Before this schema can be built](#10-before-this-schema-can-be-built)

---

## 1. What a star schema is

A star schema is a warehouse layout with **one fact table in the center** and **dimension tables around it**. The picture looks like a star: the fact is the hub, and each dimension is a point.

**The fact table** stores the event you want to measure. Here that event is a card purchase: one amount, one timestamp, one row. Each row holds numeric measures (`amount`, later `risk_score` and `z_score`) plus foreign keys that point at the dimensions.

**A dimension table** stores the nouns you filter and group by: the customer, the card, the merchant, the calendar day. Those columns are attributes, not measures. You do not sum `card_brand`. You use it to slice a sum of `amount`.

```text
                    dim_client
                         |
                         |
  dim_date ------ fact_transactions ------ dim_merchant
                         |
                         |
                      dim_card
```

A query for "high-risk dollars by merchant category last quarter" joins the fact to `dim_merchant` and `dim_date`, filters the date, and sums `amount`. The join path is short because every dimension connects only to the fact.

**Star vs. snowflake.** A star joins dimensions directly to the fact. A snowflake splits a dimension further (for example, category as its own table under merchant). This portfolio stays a star so the Power BI model stays one hop from the fact.

---

## 2. Why analysts and BI tools use it

| Benefit | What it gives you |
| --- | --- |
| One grain | You can say what a fact row means. Each amount is counted once. |
| Short joins | A business question is `fact` plus one or two dimensions. That is the pattern Power BI relationships expect. |
| Reusable descriptions | Merchant category lives in one table. A rename updates that table; history on the fact does not need a rewrite. |
| Clear filters | Slicers (year, brand, category, risk tier) sit on dimensions. KPI cards sit on measures in the fact. |

---

## 3. Terms

| Term | Meaning in this project |
| --- | --- |
| Grain | What one fact row represents. Target: one card transaction. |
| Measure | A number you aggregate. `amount` is a measure. `card_brand` is not. |
| Attribute | A descriptive column on a dimension, used to filter or group. |
| Primary key | The unique id of a dimension row, or `transaction_id` on the fact. |
| Foreign key | A column on the fact that points at a dimension primary key. |
| Natural key | An id from the source system, such as `client_id` or card `id`. |
| Surrogate key | A warehouse-generated integer with no meaning in the source, such as `date_key`. |
| Degenerate dimension | An attribute kept on the fact because it has no useful dimension table (`flag_type`, `transaction_id`). |

On the fact table, foreign keys use the **same names** as the dimension primary keys (`card_id`, `client_id`, `merchant_id`, `date_key`). That keeps Power BI relationships obvious.

---

## 4. Grain comes first

Before writing `CREATE TABLE`, finish this sentence:

> One row in `fact_transactions` is one **card transaction**.

That decision fixes everything else.

- Customer attributes do not belong on the fact. A customer has many transactions.
- Transaction amount does not belong on `dim_client`. The amount changes every purchase.

If the grain is wrong, totals double-count.

| Wrong grain | What breaks |
| --- | --- |
| One row per card per day | You cannot count purchases. |
| One row per customer | You cannot say which merchant. |

---

## 5. What the warehouse holds today

`data/financial_warehouse.db` contains one table, `raw_transactions`, loaded from `data/raw/cards_data.csv`.

| | |
| --- | --- |
| Rows | 6,146 |
| Grain | One row per card |
| Missing | Purchase amount, merchant, transaction timestamp |

That file is a **dimension source**, not a fact source. Naming it `raw_transactions` does not make it a fact table.

Card brand, credit limit, and open date describe a card. They do not record something that happened at a point in time with a dollar measure you can sum across events.

`card_number` and `cvv` are excluded from every analytical table. They are secrets, not attributes a risk dashboard needs.

### How today's columns map

| Staging column | Role | Lands in |
| --- | --- | --- |
| `id` | Card natural key | `dim_card.card_id` |
| `client_id` | Client natural key | `dim_client.client_id` and `dim_card.client_id` |
| `card_brand` | Card attribute | `dim_card` |
| `card_type` | Card attribute | `dim_card` |
| `has_chip` | Card attribute | `dim_card` |
| `num_cards_issued` | Card attribute | `dim_card` |
| `credit_limit` | Card attribute, currently text like `$24295` | `dim_card.credit_limit` as a number |
| `acct_open_date` | Card attribute, currently `MM/YYYY` | `dim_card` as a date |
| `expires` | Card attribute | `dim_card` |
| `year_pin_last_changed` | Card attribute | `dim_card` |
| `card_on_dark_web` | Card attribute | `dim_card` |
| `card_number` | Secret | Nowhere in the model |
| `cvv` | Secret | Nowhere in the model |

`credit_limit` belongs on `dim_card` because it describes the card. It is not a transaction measure. Summing it across purchases would repeat the same limit once per row and inflate the total.

---

## 6. Target model

The fact table waits on a transactions file: one row per purchase, with amount, datetime, card id, and merchant. The card file already loaded becomes `dim_card`.

### `fact_transactions`

Grain: one row per transaction.

| Column | Kind | Notes |
| --- | --- | --- |
| `transaction_id` | Primary key | Natural key from the transaction source. Also a degenerate dimension. |
| `date_key` | Foreign key | To `dim_date.date_key`. Integer date, for example `20240315`. |
| `card_id` | Foreign key | To `dim_card.card_id`. |
| `client_id` | Foreign key | To `dim_client.client_id`. Stored on the fact so client reports do not hop through the card. |
| `merchant_id` | Foreign key | To `dim_merchant.merchant_id`. |
| `amount` | Measure | Numeric dollars. |
| `risk_score` | Measure | Filled by the anomaly step. |
| `z_score` | Measure | Distance from that customer's own history. |
| `flag_type` | Degenerate dimension | Short code with no table of its own: `structuring`, `statistical_outlier`. |

### `dim_card`

Grain: one row per card. Built from the current staging table.

| Column | Notes |
| --- | --- |
| `card_id` | Primary key (from staging `id`) |
| `client_id` | Foreign key to `dim_client` |
| `card_brand` | Visa, Mastercard, and so on |
| `card_type` | Debit, credit, and so on |
| `has_chip` | |
| `num_cards_issued` | |
| `credit_limit` | Numeric, parsed from `$24295` |
| `acct_open_date` | Date, parsed from `MM/YYYY` |
| `expires` | |
| `year_pin_last_changed` | |
| `card_on_dark_web` | |

### `dim_client`

Grain: one row per client.

Built from the distinct `client_id` values on the card file until a customer file arrives. Later attributes (signup date, risk tier, credit score) land here when a source has them.

| Column | Notes |
| --- | --- |
| `client_id` | Primary key |

### `dim_merchant`

Grain: one row per merchant. Comes from the transaction source, not from the card file.

| Column | Notes |
| --- | --- |
| `merchant_id` | Primary key |
| `merchant_name` | |
| `category` | Stays on this table, not on the fact |
| `city` | |
| `state` | |
| `risk_level` | |

Category stays on `dim_merchant`. Putting category text on every fact row copies it onto every purchase. A rename then requires an update to history. On the dimension, the category is stored once.

### `dim_date`

Grain: one row per calendar day.

Generated in SQL for the min-to-max span of transaction dates, not only the days that happen to have a purchase.

| Column | Notes |
| --- | --- |
| `date_key` | Primary key, integer `YYYYMMDD` |
| `full_date` | Calendar date |
| `year` | |
| `quarter` | |
| `month` | |
| `month_name` | |
| `day` | |
| `day_name` | |
| `is_weekend` | |

A continuous calendar makes "no transactions on Sunday" visible. If the dimension only contains dates that had a purchase, empty days disappear and time-intelligence comparisons get holes.

---

## 7. Load order

Order matters because the fact's foreign keys have to already exist.

1. Clean staging: parse `$24295` into `24295`, parse `09/2002` into a date, drop or quarantine rows with a null card id.
2. Insert distinct clients into `dim_client`.
3. Insert cards into `dim_card`.
4. Generate `dim_date` for the transaction date range.
5. Insert distinct merchants into `dim_merchant`.
6. Insert into `fact_transactions` by joining transaction staging rows to those dimensions.

After the load, this check should balance:

```text
staging transaction rows
  = fact rows
  + rows rejected for a missing card, client, merchant, or date
```

That reconciliation is the proof the model did not silently drop purchases.

---

## 8. Power BI relationships

Each relationship is **one-to-many** from the dimension to the fact, **single direction** (the dimension filters the fact).

```text
dim_date[date_key]            1 ─── *  fact_transactions[date_key]
dim_card[card_id]             1 ─── *  fact_transactions[card_id]
dim_client[client_id]         1 ─── *  fact_transactions[client_id]
dim_merchant[merchant_id]     1 ─── *  fact_transactions[merchant_id]
```

Filter direction stays single so a selection on merchant category filters transactions, and those transactions do not automatically filter unrelated clients through the fact. Bidirectional filters are a later choice for a specific visual, not the default.

Measures (`Total Volume`, `High-Risk Volume`, `Flagged Rate`) live in a measure table or on the fact. They are not stored columns unless the value is an input to the measure, such as `amount` itself.

---

## 9. How the three questions use this schema

| Business question | Uses |
| --- | --- |
| Who has a burst of payments just under a threshold? | `fact_transactions.amount` and the date, partitioned by `client_id` |
| Which categories concentrate high-risk dollars? | `SUM(amount)` by `dim_merchant.category`, filtered to flagged rows |
| How does this month compare with last year and with the customer's own baseline? | `dim_date` time intelligence, plus `z_score` computed within `client_id` |

---

## 10. Before this schema can be built

1. Add a transactions source with amount, datetime, card id, and merchant.
2. Profile it: row count, date range, null keys, duplicate transaction ids, amounts that are zero or negative.
3. Create `dim_card` and `dim_client` from the card file already in `raw_transactions`.
4. Create `dim_merchant`, `dim_date`, and `fact_transactions` from the transactions source.
5. Run the reconciliation check, then point Power BI at these four dimensions and one fact.
