
# Marketplace Seller Performance Pipeline

An end-to-end data engineering solution built to process Brazilian e-commerce marketplace data, calculate seller performance metrics, track commissions, attribute marketing campaigns, and expose business insights through REST APIs.

The project uses the Brazilian Olist e-commerce dataset and implements data ingestion, transformation, quality validation, dimensional modelling, business-rule processing, and API development.

## Business Objectives

- Build a reliable pipeline for marketplace transaction data.
- Track seller performance across monthly periods.
- Calculate seller commissions using effective-dated commission rules.
- Measure delivery SLA and seller delivery performance.
- Convert Brazilian Real (BRL) values into US Dollars (USD).
- Attribute eligible order items to marketing campaigns.
- Enrich customer and seller data with Brazilian geographic information.
- Expose operational and analytical insights through REST APIs.
- Record data quality issues and pipeline execution details.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python |
| Data Processing | Pandas, NumPy |
| Database | MySQL 8 |
| Database Connectivity | SQLAlchemy, PyMySQL |
| API Development | FastAPI |
| API Server | Uvicorn |
| Testing | Pytest, FastAPI TestClient |
| External APIs | Frankfurter, Nager.Date, BrasilAPI |
| Version Control | Git, GitHub |

## Architecture

```text
             Olist Source CSVs
                     |
                     v
              Bronze Layer
             Raw Source Data
                     |
                     v
              Silver Layer
       Cleaning and Standardization
                     |
                     v
             MySQL Database
                     |
          +----------+----------+
          |          |          |
          v          v          v
       Business   Reference   Data Quality
       Processing    Data       Tracking
          |          |          |
          +----------+----------+
                     |
                     v
             Analytical Tables
                     |
                     v
               FastAPI Layer
                     |
                     v
           Business Performance
                 Insights
```

## Repository Structure

```text
marketplace-seller-performance-pipeline/
|
├── data/
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── internal/
│       ├── campaigns.json
│       ├── category_translation_patch.csv
│       ├── commission_rates.csv
│       ├── category_commission_overrides.csv
│       └── brazil_states_fallback.json
|
├── src/
│   ├── api.py
│   ├── profile_bronze.py
│   ├── transform_silver.py
│   ├── transform_reference_data.py
│   ├── transform_transaction_data.py
│   ├── transform_geolocation.py
│   ├── load_dimensions.py
│   ├── load_orders.py
│   ├── load_order_items.py
│   ├── load_payments.py
│   ├── extract_fx_rates.py
│   ├── load_fx_rates.py
│   ├── extract_holidays.py
│   ├── load_holidays.py
│   ├── calculate_delivery_sla.py
│   ├── calculate_seller_tiers.py
│   ├── calculate_commissions.py
│   ├── load_reviews.py
│   ├── load_geolocation.py
│   ├── calculate_seller_customer_distance.py
│   ├── extract_brazil_states.py
│   ├── load_brazil_states.py
│   ├── load_campaigns.py
│   ├── attribute_campaigns.py
│   ├── resolve_product_categories.py
│   └── update_product_categories.py
|
├── sql/
├── tests/
│   └── test_api.py
├── docs/
├── screenshots/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── ASSUMPTIONS.md
└── RESULTS.md
```

*Note: Bronze, Silver, and Gold generated datasets are excluded from GitHub. The internal configuration files are maintained in the repository.*

## Data Pipeline

### 1. Data Ingestion

The pipeline processes the following Olist datasets:

- Customers
- Sellers
- Orders
- Order Items
- Payments
- Reviews
- Products
- Geolocation
- Product Category Translations

External data sources:

| Source | Purpose |
|---|---|
| Frankfurter API | BRL to USD exchange rates |
| Nager.Date API | Brazilian national and regional holidays |
| BrasilAPI / IBGE | Brazilian state reference information |

### 2. Data Transformation

The Silver layer performs:

- Column name standardization.
- String trimming and normalization.
- Duplicate business-key identification.
- Timestamp parsing.
- Geolocation bounding-box filtering.
- ZIP-code-level median coordinate calculation.
- Product category translation resolution.

### 3. MySQL Data Model

The database contains dimension, fact, reference, bridge, and operational tables.

**Dimension tables**
- `dim_customer`
- `dim_seller`
- `dim_product`
- `dim_date`
- `dim_campaign`

**Fact tables**
- `fact_order`
- `fact_order_item`
- `fact_order_payment`
- `fact_order_review`

**Reference and supporting tables**
- `ref_fx_rate`
- `ref_holiday`
- `ref_commission_rate`
- `ref_category_commission_override`
- `ref_geolocation`
- `ref_brazil_state`
- `seller_monthly_tier`
- `bridge_seller_review`
- `bridge_campaign_target`

**Operational tables**
- `data_quality_issue`
- `pipeline_run`

## Business Rules Implemented

The pipeline implements the assignment's R1–R18 business rules, covering:

- Customer identity resolution.
- Revenue eligibility based on order status.
- Delivery timestamp quality checks.
- Gross merchandise value and payment reconciliation.
- Effective-dated foreign exchange conversion.
- Monetary precision using MySQL DECIMAL.
- Product category translation precedence.
- Business-day delivery SLA calculations.
- On-time delivery classification.
- Seller versus carrier delay classification.
- Monthly seller tier calculation.
- Effective-dated seller commission calculation.
- Latest review selection and seller attribution.
- Geographic ZIP-code coordinate aggregation.
- Seller-to-customer distance calculation.
- Brazilian state and region enrichment.
- Campaign attribution using date, geography, category, and priority.

See `ASSUMPTIONS.md` for implementation decisions and limitations.

## API Endpoints

The FastAPI application exposes the following endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | API and database health |
| GET | `/orders/{order_id}` | Order details |
| GET | `/sellers/{seller_id}/scorecard?month=YYYY-MM` | Monthly seller scorecard |
| GET | `/sellers/top?month=YYYY-MM&metric=commission_usd&limit=10` | Top sellers |
| GET | `/kpis/monthly?start=YYYY-MM&end=YYYY-MM&region=Sul` | Monthly regional KPIs |
| GET | `/campaigns/{campaign_id}/performance` | Campaign performance |
| GET | `/data-quality/summary?run_id=1` | Data quality summary |

### Run the API

```bash
uvicorn src.api:app --reload
```

Open interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### Example API Requests

```bash
curl http://127.0.0.1:8000/health
```

```bash
curl "http://127.0.0.1:8000/sellers/top?month=2018-03&metric=commission_usd&limit=5"
```

```bash
curl http://127.0.0.1:8000/campaigns/C001/performance
```

## Setup and Installation

### Prerequisites

- Python 3.10 or later
- MySQL 8.x
- Git

### 1. Clone the repository

```bash
git clone https://github.com/deepakyadav-pipelines/marketplace-seller-performance-pipeline.git

cd marketplace-seller-performance-pipeline
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv

source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Update `.env` with your local MySQL credentials:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=marketplace_db
```

### 5. Create the database

Create the database in MySQL:

```sql
CREATE DATABASE marketplace_db;
```

Execute the schema script in the `sql/` directory before running the loaders.

### 6. Prepare source data

Place the required Olist CSV files in `data/bronze/`.

Place the internal configuration files in `data/internal/`.

### 7. Execute pipeline scripts

Execute ingestion, transformation, reference-data loading, business-rule processing, and campaign attribution scripts in their dependency order.

Generated datasets are written to the Silver layer, while processed business data is stored in MySQL.

*Important: Several loaders are append-oriented. Do not rerun them against an already populated database without resetting or implementing an appropriate incremental load strategy.*

## Testing

Run the automated tests:

```bash
python -m pytest -q
```

The current test suite includes API health checks, successful endpoint responses, invalid inputs, and not-found scenarios.

## External API Limitations

The BrasilAPI and IBGE state-reference endpoints were unavailable during execution. A static fallback containing 27 Brazilian state and Federal District records was used to complete geographic enrichment.

The fallback is maintained in:

```text
data/internal/brazil_states_fallback.json
```

This should not be interpreted as a successful live API extraction.

## Documentation

- `ASSUMPTIONS.md` - Business-rule assumptions and implementation decisions.
- `RESULTS.md` - Execution metrics, validation results, and analytical findings.

## Security

- Never commit `.env` or database credentials.
- Keep generated source datasets out of version control.
- Use `.env.example` for configuration documentation.
- Avoid committing confidential or sensitive information.
