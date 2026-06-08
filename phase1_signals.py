"""
MA Crossover Backtester — Phase 1 & 2
Fetches Nifty 50 price data and generates Golden/Death Cross signals.
"""

import pandas as pd
import numpy as np
import yfinance as yf
import os
import warnings
warnings.filterwarnings("ignore")

# ── 1. UNIVERSE ──────────────────────────────────────────────────────────────

NIFTY50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS",
    "SUNPHARMA.NS", "ULTRACEMCO.NS", "BAJFINANCE.NS", "WIPRO.NS", "ONGC.NS",
    "NTPC.NS", "POWERGRID.NS", "NESTLEIND.NS", "M&M.NS", "TATAMOTORS.NS",
    "TATASTEEL.NS", "JSWSTEEL.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS",
    "GRASIM.NS", "HCLTECH.NS", "TECHM.NS", "DIVISLAB.NS", "DRREDDY.NS",
    "CIPLA.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "BAJAJFINSV.NS", "BAJAJ-AUTO.NS",
    "BRITANNIA.NS", "HINDALCO.NS", "INDUSINDBK.NS", "SBILIFE.NS", "HDFCLIFE.NS",
    "BPCL.NS", "IOC.NS", "TATACONSUM.NS", "APOLLOHOSP.NS", "UPL.NS"
]

START_DATE = "2019-01-01"
END_DATE   = "2024-12-31"
SHORT_WIN  = 50    # Golden/Death Cross uses 50-day
LONG_WIN   = 200   # and 200-day MA


# ── 2. FETCH DATA ─────────────────────────────────────────────────────────────

def fetch_prices(tickers, start, end):
    """Download adjusted close prices for all tickers."""
    print(f"Downloading data for {len(tickers)} stocks ({start} to {end})...")
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)

    # yfinance returns multi-level columns when multiple tickers
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]]
        prices.columns = tickers

    # Drop stocks with >10% missing data
    missing_pct = prices.isna().mean()
    good = missing_pct[missing_pct < 0.10].index.tolist()
    dropped = [t for t in tickers if t not in good]
    if dropped:
        print(f"  Dropped (too much missing data): {dropped}")

    prices = prices[good].ffill()  # forward-fill minor gaps
    print(f"  Clean universe: {len(good)} stocks\n")
    return prices


# ── 3. MOVING AVERAGES & SIGNALS ──────────────────────────────────────────────

def compute_signals(prices, short=SHORT_WIN, long=LONG_WIN):
    """
    For each stock, compute MAs and generate crossover signals.

    Signal logic:
        +1  = Golden Cross (50MA crosses above 200MA) → BUY
        -1  = Death Cross  (50MA crosses below 200MA) → SELL
         0  = no change
    """
    ma_short = prices.rolling(short).mean()
    ma_long  = prices.rolling(long).mean()

    # Position: 1 when 50MA > 200MA (in an uptrend), 0 otherwise
    position = (ma_short > ma_long).astype(int)

    # Signal fires on the day position CHANGES
    signal = position.diff()
    # +1 = just turned bullish (Golden Cross)
    # -1 = just turned bearish (Death Cross)

    return ma_short, ma_long, position, signal


# ── 4. SIGNAL SUMMARY ─────────────────────────────────────────────────────────

def summarise_signals(signal, prices):
    """Print a readable summary of all crossover events."""
    records = []
    for ticker in signal.columns:
        events = signal[ticker].dropna()
        golden = events[events == 1].index.tolist()
        death  = events[events == -1].index.tolist()
        for d in golden:
            records.append({"Ticker": ticker, "Date": d, "Signal": "Golden Cross ✅", "Price": round(prices.loc[d, ticker], 2)})
        for d in death:
            records.append({"Ticker": ticker, "Date": d, "Signal": "Death Cross  ❌", "Price": round(prices.loc[d, ticker], 2)})

    df = pd.DataFrame(records).sort_values("Date").reset_index(drop=True)
    return df


# ── 5. SAVE OUTPUTS ───────────────────────────────────────────────────────────

def save_outputs(prices, ma_short, ma_long, position, signal, signal_df):
    os.makedirs("outputs", exist_ok=True)
    prices.to_csv("outputs/prices.csv")
    ma_short.to_csv("outputs/ma_50.csv")
    ma_long.to_csv("outputs/ma_200.csv")
    position.to_csv("outputs/position.csv")
    signal.to_csv("outputs/signal.csv")
    signal_df.to_csv("outputs/signal_events.csv", index=False)
    print("Saved to outputs/")


# ── 6. MAIN ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Fetch
    prices = fetch_prices(NIFTY50, START_DATE, END_DATE)

    # Compute
    ma_short, ma_long, position, signal = compute_signals(prices)

    # Summarise
    signal_df = summarise_signals(signal, prices)

    # Print sample
    print("=== SAMPLE SIGNAL EVENTS (first 20) ===")
    print(signal_df.head(20).to_string(index=False))
    print(f"\nTotal crossover events detected: {len(signal_df)}")
    print(f"  Golden Crosses: {(signal_df['Signal'].str.contains('Golden')).sum()}")
    print(f"  Death Crosses:  {(signal_df['Signal'].str.contains('Death')).sum()}")

    # Save
    save_outputs(prices, ma_short, ma_long, position, signal, signal_df)

    print("\nPhase 1 & 2 complete. Run phase2_portfolio.py next.")
