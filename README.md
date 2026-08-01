# Retail Analytics Pipeline

## Overview

Retail Analytics Pipeline is an end-to-end data engineering project that transforms a raw denormalized retail transaction export into a clean analytics database.

The source data comes from a legacy operational system where customer, product, category, branch, sales, and inventory information are stored together in one large CSV file.

The goal of this project is to:

- Clean and standardize raw data
- Remove duplicates and invalid records
- Normalize data into dimension and fact tables
- Store analytics data in PostgreSQL
- Generate business insights using SQL
- Create visual reports using Matplotlib


## Business Questions

The analytics platform helps answer questions such as:

- Which products generate the highest revenue?
- Which branches have the best sales performance?
- How does revenue change over time?
- Which categories generate the highest profit?
- Which customers have the highest lifetime value?
- Which products are at risk of stockout?


# Architecture

```text
Raw CSV File
     |
     v
Data Profiling & Cleaning
(Pandas / NumPy)
     |
     v
Data Transformation
     |
     v
Normalized Dimension & Fact Tables
     |
     v
PostgreSQL Database
     |
     v
SQL Analytics
     |
     v
Reports & Visualizations
(Matplotlib)
```


# Project Structure

```text
retail-sales-analytics/

├── data/
│   ├── raw/
│   │   └── Raw legacy CSV input file
│   │
│   └── processed/
│       ├── dim_customers.csv
│       ├── dim_products.csv
│       ├── dim_categories.csv
│       ├── dim_branches.csv
│       ├── fact_sales.csv
│       └── fact_inventory_snapshot.csv


├── src/
│   ├── extract.py
│   │   Extract raw data and generate profiling information
│   │
│   ├── transform.py
│   │   Clean data and create normalized datasets
│   │
│   ├── quality.py
│   │   Run data validation checks
│   │
│   ├── load.py
│   │   Load processed data into PostgreSQL
│   │
│   ├── reports.py
│   │   Generate charts and analytics reports
│   │
│   ├── config.py
│   │   Manage environment configuration
│   │
│   └── main.py
│       Run the complete ETL pipeline


├── sql/
│   ├── 01_create_schema.sql
│   │   Create database tables
│   │
│   ├── 02_create_analytics_views.sql
│   │   Create analytical views
│   │
│   └── 03_analysis_queries.sql
│       Business analysis queries


├── reports/
│   ├── charts/
│   │   Generated charts
│   │
│   └── summary_report.md
│       Business summary report


├── docker-compose.yml
│   PostgreSQL service configuration


├── Dockerfile
│   Python application container


├── requirements.txt
│   Python dependencies


└── README.md
    Project documentation
```


# Data Model

The original CSV file contains repeated information about:

- Customers
- Products
- Categories
- Branches
- Sales transactions
- Inventory


The pipeline separates this data into a warehouse-style model.


## Dimension Tables

Dimension tables store descriptive information.

### dim_customers

Contains customer information:

- customer_id
- customer name
- email
- phone
- city
- signup date


### dim_products

Contains product information:

- product_id
- product name
- category reference
- unit cost
- unit price


### dim_categories

Contains product category information.


### dim_branches

Contains branch information:

- branch name
- city
- sales channel


## Fact Tables

Fact tables store measurable business events.


### fact_sales

Stores sales transactions:

- sale date
- customer_id
- product_id
- branch_id
- quantity
- revenue
- discount
- profit


### fact_inventory_snapshot

Stores inventory information:

- snapshot date
- product_id
- branch_id
- stock quantity
- reorder level


# ETL Pipeline

## 1. Extract

The extract phase:

- Reads the raw CSV file
- Validates required columns
- Checks file availability
- Profiles data quality
- Calculates null counts and duplicate records


## 2. Transform

The transformation phase:

- Standardizes column names
- Removes extra whitespace
- Normalizes text values
- Converts date formats
- Removes duplicate records
- Handles missing values
- Creates dimension tables
- Creates fact tables
- Calculates:

  - gross revenue
  - discount amount
  - net revenue
  - gross profit
  - margin percentage


## 3. Data Quality

The pipeline validates:

- Primary key uniqueness
- Required fields
- Foreign key relationships
- Negative values
- Invalid transactions
- Inventory constraints


Invalid records are stored separately for review.


## 4. Load

The load phase:

- Connects to PostgreSQL
- Creates database tables
- Loads dimension tables first
- Loads fact tables afterward
- Uses transactions
- Prevents duplicate loading


## 5. Analyze

SQL analytics generate:

- Daily revenue trends
- Product revenue ranking
- Branch performance
- Category profitability
- Customer lifetime value
- Stockout risk


## 6. Visualize

Matplotlib generates:

- Daily revenue chart
- Top products chart
- Branch revenue chart
- Category margin chart
- Stockout risk chart


# Technologies

## Programming

- Python
- Pandas
- NumPy


## Database

- PostgreSQL
- SQL


## Infrastructure

- Docker
- Docker Compose


## Visualization

- Matplotlib


# Setup Instructions

## 1. Clone Repository

```bash
git clone <repository-url>

cd retail-sales-analytics
```


## 2. Create Virtual Environment

```bash
python -m venv .venv
```


Activate environment:

Mac/Linux:

```bash
source .venv/bin/activate
```


## 3. Install Dependencies

```bash
pip install -r requirements.txt
```


## 4. Configure Environment Variables

Create a `.env` file:

```env
POSTGRES_DB=retail
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```


## 5. Start PostgreSQL

```bash
docker compose up -d
```


## 6. Run Pipeline

```bash
python src/main.py
```


# Git Workflow

The project uses the following branch strategy:

```text
main
 |
develop
 |
feature/*
```


## Creating a Feature Branch

```bash
git checkout develop

git pull origin develop

git checkout -b feature/task-name
```


## Completing a Feature

```bash
git add .

git commit -m "Describe your change"

git push origin feature/task-name
```


After pushing, create a Pull Request into the `develop` branch.


# Team Development Notes

Before starting work:

```bash
git pull origin develop
```
s