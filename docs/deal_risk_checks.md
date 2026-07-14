# Deal Risk Checks

This document gives the deal-analysis agent a simple risk vocabulary. The first agent should only use checks supported by data. It should not invent missing property facts.

## First Version Risk Flags

Use these flags for the initial agent:

### Missing Estimated Rent

Flag when `EstimatedAnnualRent` is missing.

Explanation:

```text
The app cannot calculate a reliable yield without an estimated annual rent. The user should verify comparable rental listings manually.
```

### Missing Net Yield

Flag when net yield is missing after calculation.

Explanation:

```text
The app could not calculate net yield for this row. This usually means a required input is missing or invalid.
```

### Negative Net Yield

Flag when recalculated net yield is below 0%.

Explanation:

```text
Under the selected assumptions, the estimated rent does not cover the modelled costs. This does not automatically mean the property is bad, but it is weak as an income-yield candidate.
```

### Unusually High Net Yield

Flag when recalculated net yield is above 10%.

Explanation:

```text
This yield is unusually high and should be checked carefully. It may reflect an inaccurate rent estimate, an unusual property type, missing costs, or a listing data issue.
```

## Later Risk Checks

Add these only after structured data is available.

### Service Charge

High service charge reduces net income. It should be treated as an annual cost when available.

Potential warning:

```text
Service charge materially reduces the yield and should be verified from the listing, agent, or lease documents.
```

### Ground Rent

Ground rent reduces net income and may have escalation terms. It should be included as an annual cost when available.

Potential warning:

```text
Ground rent should be checked for escalation clauses and lender acceptability.
```

### Lease Length

Lease length matters for resale, mortgageability, and potential lease extension cost. A lease below 80 years is commonly treated as a serious warning because marriage value can become relevant in lease extension calculations.

Potential warning:

```text
Lease length may affect mortgageability and resale value. The user should verify the remaining term before treating the result as attractive.
```

### Size

Square metres or square feet can support value checks such as price per square metre and rent per square metre.

Potential warning:

```text
Without floor area, the app cannot compare price per square metre or judge whether rent is realistic for the property size.
```

## Agent Language Rules

Use cautious wording:

```text
This looks like a candidate to investigate.
```

Avoid definitive wording:

```text
This is safe to buy.
```

Use data-grounded explanation:

```text
This ranks highly because the estimated rent is high relative to asking price under the selected mortgage assumptions.
```

Avoid unsupported explanation:

```text
This area is definitely improving.
```

## Manual Checks To Suggest

The agent may suggest the user check:

- Whether estimated rent is realistic.
- Service charge.
- Ground rent.
- Lease length.
- Tenure.
- Council tax band.
- EPC rating.
- Licensing requirements.
- Condition and refurbishment.
- Mortgage product fees.
- SDLT and purchase costs.

These are checks, not conclusions.
