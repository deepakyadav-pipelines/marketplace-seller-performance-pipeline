
# Pipeline Execution Results

## 1. Dataset Processing Summary

| Dataset | Records |
|---|---:|
| Customers | 99,441 |
| Sellers | 3,095 |
| Products | 32,951 |
| Orders | 99,441 |
| Order Items | 112,650 |
| Payments | 103,886 |
| Reviews (latest per order) | 98,673 |
| Geolocation ZIP prefixes | 19,010 |

## 2. Order Eligibility — R2

Only delivered orders are revenue eligible.

| Order Status | Total Orders | Revenue Eligible | Excluded |
|---|---:|---:|---:|
| Approved | 2 | 0 | 2 |
| Canceled | 625 | 0 | 625 |
| Created | 5 | 0 | 5 |
| Delivered | 96,478 | 96,478 | 0 |
| Invoiced | 314 | 0 | 314 |
| Processing | 301 | 0 | 301 |
| Shipped | 1,107 | 0 | 1,107 |
| Unavailable | 609 | 0 | 609 |
| **Total** | **99,441** | **96,478** | **2,963** |

## 3. Revenue Summary

| Metric | Result |
|---|---:|
| January 2018 gross USD | 354,355.38 |

Gross USD is calculated from item gross value converted using the selected FX rate.

## 4. Delivery Performance by Region — 2018

| Region | Delivered Orders | On-Time Orders | Late Orders | On-Time Rate |
|---|---:|---:|---:|---:|
| Centro-Oeste | 3,113 | 2,866 | 247 | 92.07% |
| Nordeste | 4,669 | 3,995 | 674 | 85.56% |
| Norte | 866 | 759 | 107 | 87.64% |
| Sudeste | 36,803 | 34,239 | 2,558 | 93.05% |
| Sul | 7,332 | 6,840 | 492 | 93.29% |

## 5. Campaign Attribution — R18

| Campaign | Attributed Items |
|---|---:|
| C001 | 2,876 |
| C002 | 72 |
| C003 | 196 |
| C004 | 927 |
| C005 | 35 |
| **Total** | **4,106** |

## 6. Data Quality Results

The DQ table retains records from repeated pipeline executions. Counts below distinguish unique cases from historical issue records.

| Rule | Issue | Unique Cases | Historical Records |
|---|---|---:|---:|
| R3 | Missing delivery timestamp | 8 | 16 |
| R5 | Payment/item mismatch | 249 | 249 |
| R9 | Delivery before approval | 61 | 122 |
| R9 | Missing approval timestamp | 14 | 28 |
| R13 | Missing commission rate during initial run | 0 currently unresolved | 309 historical |
| R14 | Review without seller mapping | 756 | 756 |
| R16 | Missing geolocation | 555 | 555 |

R3 and R9 issues were logged in two SLA executions. R13's initial missing-rate records were created before historical seller-tier records were added. The subsequent commission calculation completed with all revenue-eligible items rated.

## 7. Internal Reference File Cleaning

| Source File | Action | Reason |
|---|---|---|
| commission_rates.csv | Corrected | Gold tier name normalized |
| category_commission_overrides.csv | Corrected | Telephony category name normalized to lowercase |
| category_commission_overrides.csv | Rejected | watches_gifts effective end date preceded its start date |

## 8. Product Category Resolution

| Resolution Source | Products |
|---|---:|
| Kaggle translation | 32,323 |
| Manual patch | 18 |
| Missing source category / uncategorized | 610 |
| Unknown | 0 |
| **Total** | **32,951** |

## 9. Top 5 Sellers — March 2018

Metric: Commission USD

| Rank | Seller ID | Commission USD |
|---:|---|---:|
| 1 | 7d13fca15225358621be4086e1eb0964 | 1,082.52 |
| 2 | 7c67e1448b00f6e969d365cea6b010ab | 999.96 |
| 3 | 4869f7a5dfa277a7dca6462dcf3b52b2 | 976.42 |
| 4 | 5dceca129747e92ff8ef7a997dc4f8ca | 791.31 |
| 5 | ba90964cff9b9e0e6f32b23b82465f7b | 663.84 |

## 10. Campaign-wise Performance — R18

The following metrics represent all campaign-attributed items. Non-revenue-eligible items are included in attributed item counts; commission is calculated only for revenue-eligible items.

| Campaign | Attributed Items | Gross (BRL) | Commission (USD) |
|---|---:|---:|---:|
| C001 — Black Friday 2017 | 2,876 | 360,475.84 | 13,867.49 |
| C002 — Back to School SP | 72 | 6,279.01 | 209.54 |
| C003 — Tech Week | 196 | 20,591.42 | 759.88 |
| C004 — Mother's Day | 927 | 146,739.76 | 5,692.70 |
| C005 — Mother's Day South | 35 | 4,505.00 | 192.23 |
| **Total** | **4,106** | **538,591.03** | **20,721.84** |

Commission USD follows the campaign-attributed items' revenue eligibility and the R6 FX conversion logic.

Manual patches covered `home_comfort`, `pc_gamer`, and `portable_kitchen_and_food_preparers`.