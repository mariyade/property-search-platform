def calculate_stamp_duty(price, is_buy_to_let=True):
    if price is None or price <= 0:
        return 0

    base = 0
    if price > 125000:
        base += 0.02 * min(price - 125000, 125000)
    if price > 250000:
        base += 0.05 * min(price - 250000, 675000)
    if price > 925000:
        base += 0.10 * min(price - 925000, 575000)
    if price > 1500000:
        base += 0.12 * (price - 1500000)

    surcharge = 0.05 * price if is_buy_to_let else 0
    return base + surcharge


def calculate_gross_yield(df_buy, avg_rent_per_postcode_room):
    def get_annual_rent(row):
        key = (row["Postcode"], row["Rooms"])
        avg_monthly = avg_rent_per_postcode_room.get(key)
        if avg_monthly is None:
            return None
        return avg_monthly * 12

    df_buy["EstimatedAnnualRent"] = df_buy.apply(get_annual_rent, axis=1)
    df_buy["Gross_Yield_%"] = (df_buy["EstimatedAnnualRent"] / df_buy["Price"]) * 100
    return df_buy


def calculate_net_yield(
    df_buy,
    void_rate=0.05,
    annual_maintenance_rate=0.01,
    management_fee_rate=0.10,
    mortgage_rate=0.0515,
    ltv=0.75,
):
    if df_buy.empty or "EstimatedAnnualRent" not in df_buy.columns:
        return df_buy

    df = df_buy.copy()
    rent_after_voids = df["EstimatedAnnualRent"] * (1 - void_rate)
    maintenance_cost = df["Price"] * annual_maintenance_rate
    management_cost = rent_after_voids * management_fee_rate
    mortgage_interest = df["Price"] * ltv * mortgage_rate
    df["Stamp_Duty"] = df["Price"].apply(calculate_stamp_duty)
    total_purchase_cost = df["Price"] + df["Stamp_Duty"]

    net_income = rent_after_voids - maintenance_cost - management_cost - mortgage_interest
    df["Net_Yield_%"] = (net_income / total_purchase_cost) * 100
    return df
