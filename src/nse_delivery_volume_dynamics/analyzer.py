"""Delivery Volume Dynamics Analytics.

Computes rolling moving averages, delivery percentage z-scores,
and institutional accumulation signals.
"""

import pandas as pd
import numpy as np

class DeliveryAnalyzer:
    """Analyzes delivery volume patterns to identify institutional accumulation."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        if "trade_date" in self.df.columns:
            self.df["trade_date"] = pd.to_datetime(self.df["trade_date"])

    def get_symbol_history(self, symbol: str) -> pd.DataFrame:
        """Returns time-series delivery statistics for a specific symbol."""
        sym_df = self.df[self.df["symbol"] == symbol.upper()].sort_values("trade_date").copy()
        if sym_df.empty:
            return pd.DataFrame()

        # Rolling 20-day delivery statistics
        sym_df["rolling_20d_delivery_pct"] = sym_df["delivery_pct"].rolling(20, min_periods=5).mean()
        sym_df["rolling_20d_traded_qty"] = sym_df["traded_qty"].rolling(20, min_periods=5).mean()
        sym_df["volume_surge_ratio"] = sym_df["traded_qty"] / sym_df["rolling_20d_traded_qty"]

        # Institutional accumulation flag:
        # High delivery % (>50%) AND Volume surge > 1.5x AND Positive daily return
        price_return = (sym_df["close_price"] - sym_df["prev_close"]) / sym_df["prev_close"]
        sym_df["is_accumulation"] = (
            (sym_df["delivery_pct"] >= 50.0) &
            (sym_df["volume_surge_ratio"] >= 1.5) &
            (price_return > 0.0)
        )
        return sym_df

    def get_top_accumulated_scrips(self, as_of_date: str = None, min_turnover_cr: float = 5.0) -> pd.DataFrame:
        """Returns scrips with highest delivery % and turnover on a given date."""
        df_target = self.df
        if as_of_date:
            df_target = df_target[df_target["trade_date"] == pd.to_datetime(as_of_date)]
        else:
            latest_date = df_target["trade_date"].max()
            df_target = df_target[df_target["trade_date"] == latest_date]

        filtered = df_target[df_target["turnover_cr"] >= min_turnover_cr].copy()
        return filtered.sort_values(by="delivery_pct", ascending=False)
