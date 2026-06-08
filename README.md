# MA Crossover Backtester — Nifty 50 (2019–2024)

A Python-based backtesting framework that tests a **Golden Cross / Death Cross moving average strategy** on the Nifty 50 stock universe over a 6-year period, benchmarked against a passive buy-and-hold approach.

---

## What This Project Does

- Pulls 6 years of adjusted daily price data for all 50 Nifty 50 stocks via `yfinance`
- Generates **Golden Cross** (50-day MA crosses above 200-day MA → buy) and **Death Cross** (50-day MA crosses below 200-day MA → sell) signals for each stock
- Simulates a ₹10,00,000 portfolio with monthly rebalancing — equal weight across all stocks with an active Golden Cross signal
- Benchmarks against an equal-weight buy-and-hold portfolio of the same universe
- Calculates full performance metrics: total return, CAGR, Sharpe ratio, max drawdown, volatility

---

## Results

| Metric | MA Crossover Strategy | Buy & Hold Benchmark |
|---|---|---|
| Total Return | +113.6% | +210.3% |
| CAGR | 13.5% | 20.8% |
| Sharpe Ratio | 0.85 | 1.11 |
| Max Drawdown | -36.7% | -36.3% |
| Volatility (p.a.) | 16.9% | 19.0% |
| Final Value (₹10L) | ₹21,35,820 | ₹31,03,142 |

**Key finding:** In the 2019–2024 period, passive buy-and-hold outperformed the MA crossover strategy on both absolute and risk-adjusted returns. The COVID-19 crash (March 2020) was too fast for the 200-day MA to generate a timely exit signal, and the V-shaped recovery penalised the strategy's delayed re-entry. This structural lag — inherent to backward-looking trend indicators — is the strategy's core vulnerability in fast crash-and-recovery cycles.

---

## Project Structure

```
ma-crossover-backtester/
│
├── phase1_signals.py        # Data fetching + MA signal generation
├── phase2_portfolio.py      # Portfolio simulation + performance analysis
│
├── outputs/                 # Generated after running the scripts
│   ├── prices.csv
│   ├── ma_50.csv
│   ├── ma_200.csv
│   ├── position.csv
│   ├── signal_events.csv
│   ├── portfolio_values.csv
│   └── backtest_results.png
│
└── MA_Crossover_Research_Paper.docx   # Full research paper
```

---

## How to Run

**1. Install dependencies**
```bash
pip install yfinance pandas numpy matplotlib
```

**2. Fetch data and generate signals**
```bash
python phase1_signals.py
```
This downloads Nifty 50 price data (2019–2024) and generates crossover signal events into `outputs/`.

**3. Run portfolio simulation**
```bash
python phase2_portfolio.py
```
This runs the backtest, prints the performance table, and saves the equity curve chart to `outputs/backtest_results.png`.

---

## How the Strategy Works

**Golden Cross → Buy**
When a stock's 50-day moving average crosses *above* its 200-day moving average, it signals that short-term momentum is outpacing the long-term trend — a bullish signal. The stock is added to the portfolio on the next monthly rebalance.

**Death Cross → Sell**
When the 50-day MA crosses *below* the 200-day MA, the stock is removed from the portfolio on the next rebalance.

**Portfolio construction**
- Rebalances on the first trading day of each month
- Equal weight allocation across all Golden Cross stocks
- 0.1% transaction cost per trade (approximates brokerage + STT)
- Fully invested when qualifying stocks exist; cash earns no return otherwise

---

## Key Takeaways

- MA crossover strategies are **trend-following** by design — they work best in prolonged bear markets (e.g. 2008) where early exit preserves capital
- In **fast crash + fast recovery** cycles like COVID-19, the strategy is penalised twice: it stays invested during the crash (signal fires too late) and re-enters late during the recovery
- The **transaction drag** from monthly rebalancing compounds over time — 72 rebalance cycles over 6 years
- For India's 2019–2024 bull market, passive exposure was the dominant strategy

---

## Tech Stack

- **Python 3** — core language
- **yfinance** — price data
- **pandas / numpy** — data processing
- **matplotlib** — visualisation

---

## Author

**Sachin** — BBA (Business Analytics), O.P. Jindal Global University  
*This project was built to learn quantitative finance concepts hands-on — signal generation, portfolio simulation, and performance attribution.*
