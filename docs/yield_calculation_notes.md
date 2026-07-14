# Yield Calculation Notes

This document describes the app's yield formulas for retrieval by the deal-analysis agent.

## Gross Yield

Gross yield measures estimated rent before costs:

```text
Gross_Yield_% = EstimatedAnnualRent / Price * 100
```

`EstimatedAnnualRent` is calculated from rental listings:

```text
EstimatedAnnualRent = average monthly rent for matching Postcode and Rooms * 12
```

For example, if a sale listing is a 2-bed property in postcode `E1 1AA`,
the app looks for rental listings with:

```text
Postcode = E1 1AA
Rooms = 2
```

It averages their monthly rent and multiplies by 12.

## Net Yield

Net yield estimates annual return after selected operating costs, mortgage interest,
and Stamp Duty purchase cost:

```text
Net_Yield_% = net annual income / total purchase cost * 100
```

The Python model:

```text
rent_after_voids = EstimatedAnnualRent * (1 - void_rate)
maintenance_cost = Price * annual_maintenance_rate
management_cost = rent_after_voids * management_fee_rate
mortgage_interest = Price * ltv * mortgage_rate
Stamp_Duty = estimated SDLT for a buy-to-let/additional property
total_purchase_cost = Price + Stamp_Duty

net_income = rent_after_voids - maintenance_cost - management_cost - mortgage_interest
Net_Yield_% = net_income / total_purchase_cost * 100
```

Stamp Duty is treated as a one-off purchase cost. It is not subtracted from annual
income; it increases the denominator used for the yield percentage.

## Default Assumptions

Defaults:

```text
void_rate = 0.05
annual_maintenance_rate = 0.01
management_fee_rate = 0.10
mortgage_rate = 0.0515
ltv = 0.75
```

Users can set `mortgage_rate` and `ltv` before starting a search.

For a cash buyer:

```text
ltv = 0
mortgage_rate = 0
```

## Recalculation Without Rescraping

Changing mortgage rate or LTV does not require another scrape. The app can recalculate
net yield from existing result rows if they include:

```text
Price
EstimatedAnnualRent
```


## What The LLM Can Say

The LLM can explain:

- Which properties rank highest under the selected assumptions.
- Whether the top results are close together or clearly separated.
- How mortgage cost changes the ranking.
- Whether a property is attractive mainly because of high estimated rent or low purchase price.
- Whether the selected assumptions are aggressive or conservative.

The LLM should not recalculate yield itself. Python should calculate, and the LLM should explain.

## Simple Flags For First Agent

Use only these initial flags:

- Missing estimated annual rent.
- Missing net yield.
- Net yield below 0%.
- Net yield above 10%.

Do not over-flag missing price or rooms if those rows are already in the final yield
table.

## Example Explanation

```text
The strongest result is the property with the highest recalculated net yield. Its gross
yield is also high, which means the rent estimate is strong relative to asking price.
The user should still verify rent and ownership costs before relying on the result.
```

## Known Limitations

The current model does not include:

- Service charge.
- Ground rent.
- Lease length.
- Lease extension cost.
- Tax position.
- Buyer-specific SDLT reliefs or exemptions.
- Refurbishment.
- Licensing.
- Local supply and demand.

These should be added as structured fields later, not guessed by the LLM.
