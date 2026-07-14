# Mortgage Assumptions And SDLT Knowledge

This document is background knowledge for the deal-analysis agent. It focuses on
mortgage assumptions and SDLT. It is not mortgage, tax, legal, or investment advice.

## User-Configurable Mortgage Inputs

The first useful mortgage inputs are:

```text
ltv
mortgage_rate
```

Optional later inputs:

```text
void_rate
annual_maintenance_rate
management_fee_rate
service_charge
ground_rent
mortgage_product_fee
legal_costs
refurbishment_budget
```

## LTV

LTV means loan-to-value:

```text
LTV = loan amount / purchase price
```

Example:

```text
Purchase price = 300,000
LTV = 75%
Loan = 225,000
Deposit = 75,000
```

If a user asks, "Could I buy this with a 15% deposit?", that means:

```text
Deposit = 15%
LTV = 85%
```

The app can calculate the implied loan and deposit, but it should not say the user will
be accepted for a mortgage. Lender criteria vary.

For buy-to-let, a 15% deposit may be difficult because many BTL products require larger
deposits than owner-occupier mortgages. The agent should phrase this cautiously:

```text
This would imply 85% LTV. The app can model the yield at 85% LTV, but lender
availability and affordability would need checking with a broker or lender.
```

## Mortgage Interest

The current yield model assumes interest-only finance:

```text
annual mortgage interest = purchase price * LTV * mortgage_rate
```

This does not repay capital. It is a yield model, not a full mortgage amortisation
schedule.

## Stress Testing

Stress testing means checking whether rent still covers mortgage cost if interest rates
are higher than the selected product rate.

For a simple app-level stress test:

```text
stressed_rate = max(user_mortgage_rate, stress_rate)
stressed_interest = price * ltv * stressed_rate
```

Then compare rent after voids with stressed interest.

Buy-to-let lenders often use rental coverage tests, commonly discussed as an interest
coverage ratio (ICR):

```text
ICR = monthly rent / monthly mortgage interest
```

The exact required ICR and stress rate are lender-specific and can vary by borrower
type, tax position, product, and whether the borrower is a portfolio landlord.

## Cash Buyer Mortgage Interest

For a cash buyer, LTV and mortgage rate can be set to zero in the app model:

```text
LTV = 0
mortgage_rate = 0
mortgage_interest = 0
```

Operating costs still need checking, including voids, maintenance, management fees,
service charge, ground rent, tax, and other ownership costs.

## SDLT

Stamp Duty Land Tax applies in England and Northern Ireland. Scotland and Wales have
different property transaction taxes.

For residential purchases, SDLT is charged on increasing portions of the property price.
As of the GOV.UK residential rates page checked on 2026-07-11:

```text
0% up to 125,000
2% on 125,001 to 250,000
5% on 250,001 to 925,000
10% on 925,001 to 1.5 million
12% above 1.5 million
```

Additional residential properties usually have a 5 percentage point surcharge on top of
the standard rates.

First-time buyer relief applies only if the buyer and anyone else buying with them are
first-time buyers, intend to occupy the property as their main residence, and the
purchase price is no more than 500,000. That means first-time buyer relief is usually
not relevant to a buy-to-let purchase where the buyer does not intend to occupy the
property as their main residence.

The app estimates Stamp Duty using the additional-property surcharge. The agent should
not present this as definitive tax advice because buyer circumstances and reliefs can
change the final amount. It can say:

```text
This may be an additional-property purchase, so SDLT surcharge could materially increase
upfront costs. Use the official calculator or a tax adviser to confirm.
```

## Source Links

- GOV.UK SDLT residential rates: https://www.gov.uk/stamp-duty-land-tax/residential-property-rates
- GOV.UK SDLT reliefs: https://www.gov.uk/guidance/stamp-duty-land-tax-relief-for-land-or-property-transactions
- Bank of England mortgage affordability test withdrawal: https://www.bankofengland.co.uk/news/2022/june/withdrawal-of-the-fpcs-affordability-test-recommendation
