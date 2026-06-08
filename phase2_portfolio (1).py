"""
MA Crossover Backtester — Phase 3 & 4 (fixed)
Portfolio simulation + performance analysis vs Nifty 50 benchmark.

Run AFTER phase1_signals.py (needs outputs/ folder)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings
warnings.filterwarnings("ignore")

# ── CONFIG ────────────────────────────────────────────────────────────────────

INITIAL_CAPITAL  = 1_000_000   # ₹10,00,000
TRANSACTION_COST = 0.001       # 0.1% per trade

# ── 1. LOAD PHASE 1 OUTPUTS ───────────────────────────────────────────────────

print("Loading data from outputs/...")
prices   = pd.read_csv("outputs/prices.csv",   index_col=0, parse_dates=True)
position = pd.read_csv("outputs/position.csv", index_col=0, parse_dates=True)

prices   = prices.sort_index()
position = position.sort_index()
dates    = prices.index

print(f"  Date range : {dates[0].date()} → {dates[-1].date()}")
print(f"  Universe   : {len(prices.columns)} stocks\n")


# ── 2. PORTFOLIO SIMULATION (clean rewrite) ───────────────────────────────────

def run_backtest(prices, position, initial_capital, tx_cost):
    """
    Monthly rebalancing simulation with correct cash accounting.
    
    Key fix: total portfolio value = cash + equity at all times.
    On rebalance day: sell everything → cash = total value * (1 - sell costs)
                      buy new stocks  → spend all cash equally across targets
    """
    cash     = initial_capital
    holdings = {}        # { ticker: shares }
    port_value = []
    current_month = None

    for date in dates:
        month = (date.year, date.month)

        if month != current_month:
            current_month = month

            # Step 1: Mark-to-market everything → get total value
            equity = sum(
                shares * prices.loc[date, ticker]
                for ticker, shares in holdings.items()
                if ticker in prices.columns and not np.isnan(prices.loc[date, ticker])
            )
            total_value = cash + equity

            # Step 2: Pay sell-side transaction costs on equity portion
            cash = total_value - equity * tx_cost
            holdings = {}

            # Step 3: Determine target stocks (Golden Cross active today)
            today_pos = position.loc[date]
            targets = today_pos[today_pos == 1].index.tolist()
            # Filter to stocks with valid prices today
            targets = [t for t in targets if t in prices.columns
                       and not np.isnan(prices.loc[date, t])
                       and prices.loc[date, t] > 0]

            # Step 4: Buy equally, paying buy-side costs
            if targets:
                alloc = cash / len(targets)
                for ticker in targets:
                    price = prices.loc[date, ticker]
                    shares = (alloc * (1 - tx_cost)) / price
                    holdings[ticker] = shares
                cash = 0.0   # fully invested

        # Daily valuation
        equity = sum(
            shares * prices.loc[date, ticker]
            for ticker, shares in holdings.items()
            if ticker in prices.columns and not np.isnan(prices.loc[date, ticker])
        )
        port_value.append(cash + equity)

    return pd.Series(port_value, index=dates, name="Strategy")


# ── 3. BENCHMARK ──────────────────────────────────────────────────────────────

def nifty50_benchmark(prices, initial_capital):
    day1 = prices.iloc[0].dropna()
    alloc = initial_capital / len(day1)
    shares = alloc / day1
    return prices[day1.index].multiply(shares, axis=1).sum(axis=1).rename("Benchmark")


# ── 4. PERFORMANCE METRICS ────────────────────────────────────────────────────

def calc_metrics(series, label):
    returns    = series.pct_change().dropna()
    total_ret  = (series.iloc[-1] / series.iloc[0] - 1) * 100
    n_years    = (series.index[-1] - series.index[0]).days / 365.25
    cagr       = ((series.iloc[-1] / series.iloc[0]) ** (1/n_years) - 1) * 100
    sharpe     = (returns.mean() / returns.std()) * np.sqrt(252)
    max_dd     = ((series - series.cummax()) / series.cummax()).min() * 100
    volatility = returns.std() * np.sqrt(252) * 100

    print(f"\n{'─'*42}")
    print(f"  {label}")
    print(f"{'─'*42}")
    print(f"  Total Return : {total_ret:+.1f}%")
    print(f"  CAGR         : {cagr:+.1f}%")
    print(f"  Sharpe Ratio : {sharpe:.2f}")
    print(f"  Max Drawdown : {max_dd:.1f}%")
    print(f"  Volatility   : {volatility:.1f}% p.a.")
    print(f"  Final Value  : ₹{series.iloc[-1]:,.0f}")

    return dict(label=label, total_return=total_ret, cagr=cagr,
                sharpe=sharpe, max_drawdown=max_dd,
                volatility=volatility, final_value=series.iloc[-1])


# ── 5. SUMMARY TABLE ──────────────────────────────────────────────────────────

def print_summary(m1, m2):
    rows = [
        ("Total Return (%)",  "total_return", ".1f"),
        ("CAGR (%)",          "cagr",         ".1f"),
        ("Sharpe Ratio",      "sharpe",        ".2f"),
        ("Max Drawdown (%)",  "max_drawdown",  ".1f"),
        ("Volatility (% pa)", "volatility",    ".1f"),
        ("Final Value (₹)",   "final_value",   ",.0f"),
    ]
    print(f"\n{'═'*52}")
    print(f"  {'Metric':<22} {'Strategy':>12} {'Benchmark':>12}")
    print(f"{'═'*52}")
    for name, key, fmt in rows:
        print(f"  {name:<22} {m1[key]:>12{fmt}} {m2[key]:>12{fmt}}")
    print(f"{'═'*52}")


# ── 6. PLOTS ──────────────────────────────────────────────────────────────────

def plot_results(strategy, benchmark, position):
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    fig.suptitle("MA Crossover Backtester — Nifty 50 Universe (2019–2024)",
                 fontsize=14, fontweight="bold")

    # Panel 1: Equity curve
    ax1 = axes[0]
    ax1.plot(strategy.index,  strategy  / strategy.iloc[0]  * 100,
             label="MA Crossover Strategy", color="#2563EB", linewidth=1.8)
    ax1.plot(benchmark.index, benchmark / benchmark.iloc[0] * 100,
             label="Buy & Hold Benchmark", color="#9CA3AF", linewidth=1.4, linestyle="--")
    ax1.set_title("Equity Curve (Indexed to 100)")
    ax1.set_ylabel("Value (base=100)")
    ax1.legend(); ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Panel 2: Drawdown
    ax2 = axes[1]
    for s, color, label in [(strategy, "#2563EB", "Strategy"),
                             (benchmark, "#9CA3AF", "Benchmark")]:
        dd = (s - s.cummax()) / s.cummax() * 100
        ax2.fill_between(dd.index, dd.values, 0, alpha=0.4, color=color, label=label)
    ax2.set_title("Drawdown (%)"); ax2.set_ylabel("Drawdown %")
    ax2.legend(); ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Panel 3: Active stocks
    ax3 = axes[2]
    active = position.sum(axis=1)
    ax3.fill_between(active.index, active.values, alpha=0.5, color="#10B981")
    ax3.set_title("Stocks Held (Golden Cross active)")
    ax3.set_ylabel("# Stocks"); ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    plt.tight_layout()
    plt.savefig("outputs/backtest_results.png", dpi=150, bbox_inches="tight")
    print("\nChart saved → outputs/backtest_results.png")
    plt.show()


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running portfolio simulation...")
    strategy  = run_backtest(prices, position, INITIAL_CAPITAL, TRANSACTION_COST)
    benchmark = nifty50_benchmark(prices, INITIAL_CAPITAL)

    common    = strategy.index.intersection(benchmark.index)
    strategy  = strategy.loc[common]
    benchmark = benchmark.loc[common]

    m1 = calc_metrics(strategy,  "MA Crossover Strategy")
    m2 = calc_metrics(benchmark, "Buy & Hold Benchmark")
    print_summary(m1, m2)

    plot_results(strategy, benchmark, position)

    pd.DataFrame({"strategy": strategy, "benchmark": benchmark}).to_csv(
        "outputs/portfolio_values.csv")
    print("Saved → outputs/portfolio_values.csv")
    print("\nPhase 3 & 4 complete.")
