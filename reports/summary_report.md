# Retail Analytics Report

## 1. Executive Summary

The Retail Analytics Pipeline transformed the retail transaction
dataset into a normalized analytical model, loaded the resulting
data into PostgreSQL, performed data-quality checks, and generated
analytical reports and visualizations.

The analytical database currently contains:

- **997,464 sales transactions**
- **50,000 customers**
- **500 products**
- **20 categories**
- **40 branches**
- **976,946 inventory snapshots**

---

## 2. Key Performance Indicators

| KPI | Value |
| --- | ---: |
| Total sales transactions | 997,464 |
| Total quantity sold | 3,212,782 |
| Gross revenue | $1,253,564,801.19 |
| Net revenue | $1,136,179,956.57 |
| Gross profit | $496,020,326.72 |
| Gross margin | 43.66% |
| Average order value | $1,139.07 |
| Customers | 50,000 |
| Products | 500 |
| Categories | 20 |
| Branches | 40 |
| Inventory snapshots | 976,946 |

---

## 3. Sales by Category

The highest-revenue category is **Toys**,
generating **$81,744,178.50** in net revenue.

### Top Categories

| Category | Revenue | Gross Profit | Gross Margin |
| --- | ---: | ---: | ---: |
| Toys | $81,744,178.50 | $40,703,796.35 | 49.79% |
| Sports | $69,379,093.11 | $33,326,601.99 | 48.04% |
| Pets | $66,555,318.67 | $31,663,486.65 | 47.57% |
| Beauty | $65,512,275.95 | $29,263,839.56 | 44.67% |
| Electronics | $63,357,431.46 | $26,381,620.38 | 41.64% |
| Grocery | $54,850,817.61 | $26,120,548.84 | 47.62% |
| Clothing | $56,847,684.14 | $25,835,486.12 | 45.45% |
| Books | $54,410,326.72 | $24,865,667.31 | 45.70% |
| Travel | $52,940,261.81 | $24,670,651.49 | 46.60% |
| Health | $61,516,245.89 | $24,012,063.75 | 39.03% |
| Furniture | $54,263,711.99 | $23,373,413.57 | 43.07% |
| Home Appliances | $56,745,853.92 | $23,338,313.65 | 41.13% |
| Music | $53,029,300.22 | $22,791,663.93 | 42.98% |
| Shoes | $54,076,299.07 | $22,714,170.75 | 42.00% |
| Office | $52,276,461.85 | $21,561,308.98 | 41.24% |
| Baby | $52,156,460.85 | $21,430,238.77 | 41.09% |
| Gaming | $46,343,127.93 | $19,977,396.32 | 43.11% |
| Automotive | $51,932,637.94 | $19,048,955.95 | 36.68% |
| Garden | $43,179,107.06 | $18,352,515.62 | 42.50% |
| Jewelry | $45,063,361.88 | $16,588,586.74 | 36.81% |

---

## 4. Top Products

The highest-revenue product is **Smart Shirt 246**,
generating **$6,688,316.32** in revenue.

### Top 10 Products by Revenue

| Product | Quantity Sold | Revenue |
| --- | ---: | ---: |
| Smart Shirt 246 | 6,328 | $6,688,316.32 |
| Eco Desk 36 | 6,624 | $6,569,219.52 |
| Mini Ball 403 | 6,385 | $6,495,971.30 |
| Classic Ball 138 | 6,555 | $6,440,484.15 |
| Pro Ball 26 | 6,830 | $6,319,594.10 |
| Basic Headphones 207 | 6,759 | $6,148,121.58 |
| Pro Shirt 245 | 6,536 | $6,027,891.36 |
| Smart Puzzle 198 | 6,561 | $5,904,243.90 |
| Eco Shirt 251 | 6,423 | $5,848,462.65 |
| Plus Cream 309 | 6,246 | $5,837,011.92 |

---

## 5. Revenue by Branch

The highest-revenue branch is **North Branch 31**,
generating **$31,869,131.12** in revenue.

### Top Branches

| Branch | City | Channel | Revenue |
| --- | --- | --- | ---: |
| North Branch 31 | Tehran | store | $31,869,131.12 |
| Bazaar Branch 23 | Rasht | mobile | $31,776,770.79 |
| Express Branch 36 | Tehran | store | $31,733,558.15 |
| Central Branch 1 | Rasht | online | $31,710,719.74 |
| North Branch 16 | Rasht | online | $31,707,600.94 |
| Central Branch 32 | Shiraz | partner | $31,641,302.62 |
| Airport Branch 30 | Mashhad | mobile | $31,613,062.02 |
| Outlet Branch 40 | Tehran | online | $31,595,681.42 |
| Express Branch 34 | Isfahan | partner | $31,566,311.70 |
| Central Branch 11 | Tehran | partner | $31,546,003.43 |

---

## 6. Category Profitability

The category with the highest gross margin is
**Toys**, with a gross margin of
**49.79%**.

---

## 7. Top Customers

The highest-value customer is **Omid Moradi**,
with total spending of **$59,006.67**
across **34 transactions**.

### Top 10 Customers

| Customer | Orders | Total Spent |
| --- | ---: | ---: |
| Omid Moradi | 34 | $59,006.67 |
| Yasin Karimi | 32 | $58,555.53 |
| Mina Moradi | 38 | $58,530.50 |
| Leila Moradi | 33 | $58,125.14 |
| Ali Mohammadi | 33 | $57,535.71 |
| Amir Salehi | 34 | $57,295.80 |
| Ali Rahimi | 26 | $56,779.30 |
| Reza Rahimi | 28 | $56,757.24 |
| Ali Moradi | 27 | $56,407.16 |
| Omid Jafari | 31 | $56,034.93 |

---

## 8. Inventory Risk

The inventory analysis identified
**1,882 inventory records**
marked as having stockout risk.

The branch with the highest number of stockout-risk products is
**Express Branch 34**, with
**67 stockout-risk products**.

Products at or below their reorder level should be reviewed
for replenishment.

### Stockout Risk by Branch

| Branch | Stockout-Risk Products |
| --- | ---: |
| Express Branch 34 | 67 |
| West Branch 8 | 62 |
| South Branch 9 | 57 |
| Airport Branch 30 | 56 |
| Bazaar Branch 4 | 54 |
| Central Branch 7 | 54 |
| North Branch 20 | 53 |
| Outlet Branch 15 | 51 |
| East Branch 38 | 51 |
| South Branch 5 | 50 |
| Express Branch 17 | 50 |
| North Branch 29 | 50 |
| Central Branch 11 | 49 |
| North Branch 31 | 49 |
| Bazaar Branch 37 | 49 |
| Outlet Branch 24 | 48 |
| Central Branch 26 | 48 |
| South Branch 33 | 48 |
| North Branch 6 | 47 |
| Bazaar Branch 14 | 47 |
| Outlet Branch 22 | 47 |
| Central Branch 1 | 46 |
| Mall Branch 2 | 46 |
| North Branch 16 | 45 |
| Bazaar Branch 25 | 44 |
| Express Branch 36 | 44 |
| Bazaar Branch 3 | 43 |
| Bazaar Branch 19 | 43 |
| Express Branch 27 | 43 |
| Central Branch 32 | 43 |
| Express Branch 28 | 42 |
| Outlet Branch 40 | 42 |
| Airport Branch 21 | 41 |
| South Branch 12 | 40 |
| Outlet Branch 13 | 40 |
| Bazaar Branch 23 | 40 |
| Mall Branch 35 | 40 |
| North Branch 18 | 38 |
| Mall Branch 39 | 38 |
| Central Branch 10 | 37 |

---

## 9. Daily Sales Trend

The daily sales report contains
**1,096 days** of sales activity.

The highest-revenue day was **2023-03-10**,
with revenue of **$1,335,573.96**.

The lowest-revenue day was **2024-03-14**,
with revenue of **$976,701.66**.

---

## 10. Data Quality

The pipeline includes post-load validation checks covering:

- Row counts
- Primary key uniqueness
- Required key fields
- Foreign key relationships
- Numeric constraints
- Revenue calculations
- Discount calculations
- Cost calculations
- Gross profit calculations
- Inventory constraints
- Duplicate inventory snapshots

Validation results should be reviewed from the dedicated
data-quality validation output before reporting the pipeline
as fully validated.

---

## 11. Generated Analytical Reports

The following CSV reports are generated:

- `daily_sales_trend.csv`
- `top_10_products.csv`
- `top_10_branches.csv`
- `category_profitability.csv`
- `top_10_customers.csv`
- `stockout_risk_products.csv`

---

## 12. Generated Visualizations

The pipeline generates the following Matplotlib charts:

- `charts/daily_revenue.png`
- `charts/top_10_products.png`
- `charts/revenue_by_branch.png`
- `charts/category_gross_margin.png`
- `charts/stockout_risk.png`

---

## 13. Conclusion

The Retail Analytics Pipeline transforms the raw retail transaction
export into a structured PostgreSQL analytical database.

The resulting analytical outputs provide visibility into:

- Sales performance
- Product performance
- Branch performance
- Category profitability
- Customer lifetime value
- Inventory stockout risk
- Daily revenue trends

The project therefore provides the required ETL, data-quality,
SQL analytics, reporting, and visualization components.
