
# Business Rules and Implementation Assumptions

This document records implementation decisions made while translating assignment requirements into the Marketplace Seller Performance Pipeline. Explicit assignment rules are distinguished from implementation choices.

## R1 — Customer Identity
- `customer_unique_id` is treated as the customer-level identity.
- Customer home state is derived from the earliest available order.
- The customer dimension retains the source customer ID and unique customer ID.

## R2 — Revenue Eligibility
- Only orders with status `delivered` are revenue eligible.
- Orders with other statuses remain loaded for operational visibility but are excluded from revenue and commission calculations.

## R3 — Missing Delivery Timestamp
- A delivered order with a missing customer delivery timestamp remains revenue eligible.
- It is excluded from delivery SLA calculations and recorded as a data-quality issue.

## R5 — Payment Reconciliation
- Payment totals are compared against item gross value (price plus freight).
- A difference greater than BRL 1 is treated as a mismatch.
- Voucher payments are excluded from `net_cash_paid_brl`.

## R6 — Foreign Exchange
- The conversion date is the payment approval date when available; otherwise, the purchase date.
- If no rate exists for the required date, the latest available earlier rate is used.
- A future exchange rate is never used as a fallback.
- The selected rate date and rate are stored with each order item.

## R8 — Product Category Resolution
- Resolution precedence is:
  1. Manual category patch.
  2. Kaggle English category translation.
  3. `unknown` when a Portuguese category exists but has no translation.
  4. `uncategorized` when the source category is missing.
- Category resolution is performed before updating the product dimension.

## R9 — Delivery Business Days
- The approval date is excluded and the delivery date is included.
- Saturdays, Sundays, Brazilian national holidays and available state holidays are excluded.
- Orders with missing approval/delivery timestamps, missing state, or delivery before approval are excluded from SLA calculation and logged.

## R10 — On-Time Delivery
- An order is on time when the customer delivery date is on or before the estimated delivery date.
- Missing actual or estimated delivery timestamps result in a NULL on-time status.

## R11 — Seller Delivery Classification
- The earliest shipping limit across all items in an order is used as the seller shipping deadline.
- A carrier handoff after this deadline is classified as `seller_late`.
- If the seller is not late but the order is late, the item is classified as `carrier_late`.
- Remaining eligible classifications are `on_time`.

## R12 — Monthly Seller Tier
- Seller tier is calculated using the previous calendar month's revenue-eligible item price, excluding freight.
- Bronze: below BRL 5,000.
- Silver: BRL 5,000 through BRL 20,000.
- Gold: above BRL 20,000.
- Sellers without previous-month eligible sales are assigned Bronze.
- Historical tier records were also generated for months needed to calculate tiers for the earliest orders.

## R13 — Commission Calculation
- An active category-specific override takes precedence over the seller-tier commission rate.
- Commission is calculated on item price, excluding freight.
- Commission is rounded to two decimal places for the final BRL and USD values.
- Internal commission files are normalized and validated before loading.
- Invalid effective-date rows are rejected and recorded in the cleaning audit.

## R14 — Review Attribution
- The latest review for an order is selected using `review_answer_timestamp`.
- A selected review is mapped to every seller associated with the order.
- Reviews belonging to orders without order items are retained but cannot be mapped to a seller; these are recorded as data-quality issues.

## R15 — Geolocation
- Geolocation records outside the assignment's Brazil bounding box are excluded.
- Median latitude and longitude are calculated per ZIP-code prefix.
- The resulting ZIP-prefix lookup is used for customer and seller coordinates.

## R16 — Seller-to-Customer Distance
- Distance is calculated using the Haversine formula.
- Earth's radius is assumed to be 6,371 kilometres.
- Distance remains NULL when either customer or seller coordinates are unavailable; missing coordinates are logged.

## R17 — Brazilian State Enrichment
- State code, state name and region are loaded from a 27-state/DF reference dataset.
- The BrasilAPI request and IBGE fallback endpoint were unavailable during execution.
- A static reference fallback was used instead; therefore, successful live API extraction is not claimed.
- Customer and seller state codes are matched against the reference dataset.

## R18 — Campaign Attribution
- Campaign geography is matched using customer state or region.
- Product category is matched against campaign category targets.
- Date-only campaign end dates are treated as inclusive through the end of that day.
- UTC campaign timestamps are converted to São Paulo local time.
- Naive source purchase timestamps are interpreted as São Paulo local timestamps.
- When multiple campaigns match, the highest priority wins, followed by the later campaign start date. Campaign ID ascending is used as a deterministic tie-breaker.
- Customer geography is used as the campaign location because the source assignment does not provide a separate delivery-location targeting field.

## General Implementation Notes
- Monetary values are stored using MySQL DECIMAL columns.
- Source data is retained in the Bronze layer; cleaned and standardized data is stored in Silver.
- Business calculations and analytical outputs are stored in MySQL.
- API endpoints expose the resulting operational and analytical data.
- Data-quality issues are recorded with rule identifiers and entity references wherever applicable.
