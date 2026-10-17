"""CLI Tool for NSE Delivery Volume Dynamics.

Usage:
    python runner.py --symbol RELIANCE
    python runner.py --top-delivery
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from nse_delivery_volume_dynamics.analyzer import DeliveryAnalyzer

def main():
    parser = argparse.ArgumentParser(description="NSE Delivery Volume Dynamics CLI")
    parser.add_argument("--symbol", help="Target equity symbol (e.g. RELIANCE, TCS, INFY)")
    parser.add_argument("--top-delivery", action="store_true", help="Show top delivery % scrips (>5 Cr turnover)")
    parser.add_argument("--min-turnover", type=float, default=5.0, help="Minimum daily turnover in Crore")
    args = parser.parse_args()

    parquet_path = Path(__file__).parent / "output" / "delivery_dynamics.parquet"
    if not parquet_path.exists():
        print("Dataset not found. Run python update.py first.")
        return

    df = pd.read_parquet(parquet_path)
    analyzer = DeliveryAnalyzer(df)

    if args.symbol:
        sym_history = analyzer.get_symbol_history(args.symbol)
        if sym_history.empty:
            print(f"No delivery records found for {args.symbol.upper()}.")
            return
        print(f"\n--- Delivery Volume Dynamics: {args.symbol.upper()} ---")
        cols = ["trade_date", "close_price", "traded_qty", "deliverable_qty", "delivery_pct", "turnover_cr", "delivery_turnover_cr"]
        print(sym_history[cols].to_string(index=False))

    elif args.top_delivery:
        top_df = analyzer.get_top_accumulated_scrips(min_turnover_cr=args.min_turnover)
        latest_date = top_df["trade_date"].max().strftime("%Y-%m-%d")
        print(f"\n--- Top Delivery Percentage Equities as of {latest_date} (Min Rs. {args.min_turnover} Cr Turnover) ---")
        cols = ["symbol", "close_price", "delivery_pct", "traded_qty", "deliverable_qty", "turnover_cr", "delivery_turnover_cr"]
        print(top_df[cols].head(20).to_string(index=False))

    else:
        distinct_syms = df["symbol"].nunique()
        latest_date = df["trade_date"].max()
        print(f"Loaded {len(df):,} delivery records across {distinct_syms} scrips as of {latest_date}.")
        print("Use --symbol <TICKER> or --top-delivery to query data.")

if __name__ == "__main__":
    main()
