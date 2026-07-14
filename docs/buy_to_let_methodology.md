# Buy-to-Let Methodology

This document is background knowledge for the app's deal-analysis agent. It explains
how the app should talk about buy-to-let results. It is not financial, tax, legal, or
mortgage advice.

## Purpose

The app compares listed properties using estimated rent, purchase price, and
user-selected mortgage assumptions. The agent should explain the numbers clearly and
point out checks the user should do before treating any property as a serious candidate.

The app should keep calculations deterministic in Python. The language model should
explain the calculated results, not invent yields or make the final investment decision.

## Current Data Flow

The app currently follows this pipeline:

1. Scrape buy listings for a search run.
2. Scrape rental listings for the same search run.
3. Clean both datasets.
4. Estimate annual rent for each sale listing.
5. Calculate gross yield.
6. Calculate net yield.
7. Store final rows in `search_run_yields`.
8. Show results sorted by `Net_Yield_%` descending.

The dashboard requests 20 rows at a time. The first page is the top 20 rows by net
yield for that search run.

## What The Agent Should Do

The agent should act as a plain-English deal analyst. For the first version, it should:

- Load the current 20 visible deals for a search run.
- Apply the user's mortgage assumptions if provided.
- Use Python-calculated yield values.
- Explain why the strongest deals rank highly.
- Explain how mortgage rate and LTV affect net yield.
- Flag simple yield issues such as negative net yield or unusually high net yield.
- Remind the user that service charge, ground rent, lease length, tax, and refurb costs
  may not be included unless those fields have been added later.

The agent should not:

- Make up missing property details.
- Treat estimated rent as guaranteed rent.
- Treat a high yield as a recommendation to buy.
- Run arbitrary SQL.
- Give regulated mortgage, tax, or legal advice.

## Core Concepts

### Purchase Price

Purchase price is the asking/listing price from the sale listing. It is used as the
denominator for gross yield. Net yield uses purchase price plus estimated Stamp Duty.

### Estimated Annual Rent

Estimated annual rent is inferred from rental listings. Rent is estimated from the
average monthly rent for matching postcode and room count, multiplied by 12.

### Gross Yield

Gross yield is a simple rent-to-price measure:

```text
Gross yield = estimated annual rent / purchase price
```

Gross yield ignores mortgage cost, void periods, management fees, maintenance, service
charge, ground rent, tax, and purchase costs.

### Net Yield

Net yield estimates the return after selected operating costs, finance costs, and
estimated Stamp Duty:

```text
Net yield = net annual income / (purchase price + Stamp Duty)
```

The current app model includes:

- Void allowance.
- Maintenance allowance.
- Management fee.
- Mortgage interest, if LTV and mortgage rate are above zero.
- Estimated Stamp Duty for a buy-to-let/additional property.

The current app model does not yet include:

- Service charge.
- Ground rent.
- Lease extension cost.
- Insurance.
- Licensing.
- Refurbishment.
- Tax.
- Buyer-specific SDLT reliefs or exemptions.
- Legal fees.
- Survey fees.
- Mortgage product fees.

## Cash Buyer Versus Mortgage Buyer

For a cash buyer, mortgage interest should be zero. In the app this can be represented
as:

```text
LTV = 0
mortgage rate = 0
```

For a mortgage buyer:

```text
loan amount = purchase price * LTV
annual mortgage interest = loan amount * mortgage rate
```

A deal can look strong for a cash buyer but weak for a leveraged buyer if mortgage interest absorbs most of the rental income.

## Agent Explanation Style

The agent should write explanations like:

```text
This property ranks first because it has the highest recalculated net yield under the selected mortgage assumptions. Its estimated rent is high relative to the asking price, so it remains ahead after mortgage interest is deducted.
```

The agent should avoid wording like:

```text
This is definitely a good investment.
```

Prefer:

```text
This is the strongest candidate in the current dataset, subject to rent verification and missing ownership-cost checks.
```

## First Version Agent Workflow

```text
START
  -> load_deals_from_search_run
  -> recalculate_net_yields_with_user_assumptions
  -> build_metrics_and_flags
  -> retrieve_methodology_notes
  -> explain_with_llm
END
```

## Useful Source Links

- GOV.UK Stamp Duty Land Tax residential rates: https://www.gov.uk/stamp-duty-land-tax/residential-property-rates
