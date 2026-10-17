"""Quality and Schema Audit for NSE Delivery Volume Dynamics Dataset."""

import pandas as pd
from pathlib import Path

def audit_quality():
    print("=" * 65)
    print(" NSE DELIVERY VOLUME DYNAMICS - DATA QUALITY AUDIT")
    print("=" * 65)

    csv_path = Path(__file__).parent / "output" / "delivery_dynamics.csv"
    parquet_path = Path(__file__).parent / "output" / "delivery_dynamics.parquet"

    assert csv_path.exists(), f"Missing {csv_path.name}"
    assert parquet_path.exists(), f"Missing {parquet_path.name}"

    df = pd.read_parquet(parquet_path)
    print(f"Total Observations Indexed: {len(df):,}")

    # Primary key null checks
    null_syms = df["symbol"].isnull().sum()
    null_dates = df["trade_date"].isnull().sum()
    null_delivery = df["delivery_pct"].isnull().sum()

    print(f"Null Symbols: {null_syms} {'[PASS]' if null_syms == 0 else '[FAIL]'}")
    print(f"Null Trade Dates: {null_dates} {'[PASS]' if null_dates == 0 else '[FAIL]'}")
    print(f"Null Delivery Percentages: {null_delivery} {'[PASS]' if null_delivery == 0 else '[FAIL]'}")

    # Value range checks: delivery_pct must be between 0 and 100
    invalid_delivery_pct = ((df["delivery_pct"] < 0.0) | (df["delivery_pct"] > 100.0)).sum()
    print(f"Invalid Delivery Pct Range (<0 or >100): {invalid_delivery_pct} {'[PASS]' if invalid_delivery_pct == 0 else '[FAIL]'}")

    # Deliverable quantity <= traded quantity
    invalid_deliv_qty = (df["deliverable_qty"] > df["traded_qty"]).sum()
    print(f"Logical Violations (Deliverable Qty > Traded Qty): {invalid_deliv_qty} {'[PASS]' if invalid_deliv_qty == 0 else '[FAIL]'}")

    # Distinct dates count
    distinct_dates = df["trade_date"].nunique()
    print(f"Distinct Trading Dates: {distinct_dates}")

    assert null_syms == 0, "Symbols contain nulls!"
    assert null_dates == 0, "Trade dates contain nulls!"
    assert invalid_delivery_pct == 0, "Delivery pct out of bounds!"

    print("=" * 65)
    print("ALL AUDIT CHECKS PASSED.")
    print("=" * 65)

if __name__ == "__main__":
    audit_quality()
