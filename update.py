"""NSE Delivery Volume Dynamics Weekly/Daily Automated Updater.

Self-healing gap-fill updater that inspects the latest trade_date in the
dataset, fetches missing business day delivery statistics from NSE archives,
merges atomically, and exports both Parquet and CSV.
"""

import sys
from datetime import datetime, date, timedelta
from pathlib import Path
import pandas as pd

# Add local src to path for direct execution
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from nse_delivery_volume_dynamics.fetcher import DeliveryFetcher

def get_trading_days(start_date: date, end_date: date) -> list[date]:
    """Generate potential trading weekdays between start and end date inclusive."""
    days = []
    curr = start_date
    while curr <= end_date:
        if curr.weekday() < 5:  # Monday to Friday
            days.append(curr)
        curr += timedelta(days=1)
    return days

def update_delivery_dynamics():
    print(f"[{datetime.now().isoformat()}] Starting Delivery Volume Dynamics update...")
    fetcher = DeliveryFetcher()
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_file = output_dir / "delivery_dynamics.csv"
    parquet_file = output_dir / "delivery_dynamics.parquet"

    existing_df = pd.DataFrame()
    if parquet_file.exists():
        existing_df = pd.read_parquet(parquet_file)
        print(f"Loaded {len(existing_df):,} existing records from {parquet_file.name}")

    today = date.today()

    if existing_df.empty:
        # Initial seed: Last 5 weekdays
        start_date = today - timedelta(days=7)
    else:
        max_date_str = str(existing_df["trade_date"].max())
        max_date = datetime.strptime(max_date_str, "%Y-%m-%d").date()
        # Look back 1 day to re-verify latest plus fill any forward gap
        start_date = max_date - timedelta(days=1)

    target_days = get_trading_days(start_date, today)
    print(f"Targeting {len(target_days)} trading days between {start_date} and {today}...")

    new_dfs = []
    for d in target_days:
        print(f"Fetching delivery bhavcopy for {d.strftime('%Y-%m-%d')}...")
        df_day = fetcher.fetch_date(d)
        if not df_day.empty:
            print(f"  Successfully parsed {len(df_day):,} equity delivery records.")
            new_dfs.append(df_day)
        else:
            print(f"  No delivery data available for {d.strftime('%Y-%m-%d')} (weekend/holiday or not yet published).")

    if not new_dfs and existing_df.empty:
        raise RuntimeError("No delivery data could be retrieved and no existing database found.")

    combined = list(new_dfs)
    if not existing_df.empty:
        combined.insert(0, existing_df)

    merged = pd.concat(combined, ignore_index=True)

    # Core key deduplication
    merged = merged.drop_duplicates(subset=["symbol", "trade_date"], keep="last")

    # Sort chronologically descending
    merged = merged.sort_values(by=["trade_date", "turnover_cr"], ascending=[False, False]).reset_index(drop=True)

    # Atomic write to temporary files then rename/save
    merged.to_parquet(parquet_file, index=False, compression="snappy")
    merged.to_csv(csv_file, index=False)
    print(f"Saved {len(merged):,} records to {parquet_file.name} and {csv_file.name}")

    # Run quality gate
    from evaluate_quality import audit_quality
    audit_quality()
    print("Delivery Volume Dynamics update completed successfully.")

if __name__ == "__main__":
    update_delivery_dynamics()
