"""Delivery Volume Dynamics Fetcher.

Downloads NSE Bhavcopy with delivery statistics (sec_bhavdata_full)
from archives.nseindia.com, extracting security-wise traded quantity,
deliverable quantity, delivery percentage, and turnover.
"""

import io
import requests
import pandas as pd
from datetime import datetime, date
from typing import Optional, List

NSE_BHAV_URL = "https://archives.nseindia.com/products/content/sec_bhavdata_full_{date_str}.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

class DeliveryFetcher:
    """Fetches end-of-day equity delivery position statistics from NSE archives."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch_date(self, target_date: date) -> pd.DataFrame:
        """Fetch delivery bhavcopy for a specific date (DDMMYYYY)."""
        date_str = target_date.strftime("%d%m%Y")
        url = NSE_BHAV_URL.format(date_str=date_str)
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return pd.DataFrame()

            df = pd.read_csv(io.StringIO(resp.text))
            df.columns = [c.strip().upper() for c in df.columns]

            # Strip whitespace across all string/object columns
            for c in df.select_dtypes(include="object").columns:
                df[c] = df[c].astype(str).str.strip()

            # Filter for standard equity trading series (EQ, BE, SM, ST)
            series_mask = df["SERIES"].isin(["EQ", "BE", "SM", "ST"])
            eq_df = df[series_mask].copy()

            # Parse Date
            eq_df["TRADE_DATE"] = target_date.strftime("%Y-%m-%d")

            # Numeric conversions
            for num_col in ["PREV_CLOSE", "OPEN_PRICE", "HIGH_PRICE", "LOW_PRICE", "CLOSE_PRICE", "TTL_TRD_QNTY", "DELIV_QTY", "DELIV_PER", "TURNOVER_LACS"]:
                if num_col in eq_df.columns:
                    eq_df[num_col] = pd.to_numeric(eq_df[num_col].astype(str).str.replace("-", ""), errors="coerce")

            # Calculate delivery turnover in Lacs and Crore
            eq_df["DELIVERY_TURNOVER_LACS"] = (eq_df["DELIV_PER"] * eq_df["TURNOVER_LACS"]) / 100.0
            eq_df["DELIVERY_TURNOVER_CR"] = eq_df["DELIVERY_TURNOVER_LACS"] / 100.0

            result = pd.DataFrame({
                "symbol": eq_df["SYMBOL"],
                "series": eq_df["SERIES"],
                "trade_date": eq_df["TRADE_DATE"],
                "prev_close": eq_df["PREV_CLOSE"],
                "open_price": eq_df["OPEN_PRICE"],
                "high_price": eq_df["HIGH_PRICE"],
                "low_price": eq_df["LOW_PRICE"],
                "close_price": eq_df["CLOSE_PRICE"],
                "traded_qty": eq_df["TTL_TRD_QNTY"],
                "deliverable_qty": eq_df["DELIV_QTY"],
                "delivery_pct": eq_df["DELIV_PER"],
                "turnover_cr": eq_df["TURNOVER_LACS"] / 100.0,
                "delivery_turnover_cr": eq_df["DELIVERY_TURNOVER_CR"],
                "source": "NSE_SEC_BHAVDATA_FULL"
            })

            # Drop any rows where core data is missing
            result = result.dropna(subset=["symbol", "trade_date", "close_price", "delivery_pct"])
            return result

        except Exception as e:
            print(f"Error fetching delivery data for {target_date}: {e}")
            return pd.DataFrame()
