
# 📈 TradeManager

**TradeManager** is an automated trading system I'm developing on MetaTrader 5. 
As a beginner, I’m exploring my own ideas for managing risk and executing multiple trading strategies in Forex. 
This project is purely for learning and experimentation. 
I’m building something I enjoy, not intended for real trading

---

## Features

- **Broker Integration** via MetaTrader 5

- **Risk Management** (trailing stop, breakeven, drawdown control, etc.)
  - Constantly monitors existing positions in MT5 and sets breakeven
  - Trailing stop automatically adjusts stop-loss as profit increases

- **Support Multi-Strategy Detect & Execute**
  - **Strategies Included**:
    - Major Trend Confidence with Quantile Regression
    - M1 Scalping based on EMA

- **Back Testing**
  - Perform historical back testing of the trading strategy to evaluate dectector performance.
  - Display the resulting number of pips gained or lost over the tested period.

- **Candlestick Pattern Detection**
  - Bullish and Bearish Engulfing
  - Hammer and Inverted Hammer
  - Morning Star and Evening Star
  - Doji and Shooting Star
  - Hanging Man, Tweezer Top and Bottom
  - Three White Soldiers and Three Black Crows

- **Candlestick Chart Plotting** with Matplotlib

---

Update your config (see `settings.py` or rename `settings_example.py` to `settings.py`) and run:

```bash
python main.py
```

Other useful script.

```bash
python .\backtest\backtest_dector.py
python .\testcase\test_candle_stick_patterns.py
```

Make sure:
- MetaTrader 5 is installed.
- The terminal is connected to the specified demo account.
- The symbol (default: `XAUUSD`) is available and visible in the MT5 Market Watch.

```bash
pip install -r requirements.txt
```
Install dependencies via pip:

---

## Recommended VS Code Extensions for Python Development

To improve code readability, formatting, and linting, use the following VS Code extensions:

- **Flake8** — Python linting tool to enforce style guide compliance.
- **Python** — Official Microsoft Python extension for IntelliSense, debugging, and more.
- **Pylance** — Fast, feature-rich language server for Python, providing advanced type checking.
- **Python Indent** — Enhances indentation behavior in Python files.
- **Black Formatter** — Automatically formats Python code using the Black code style.
- **Python Path** — Helps manage and configure the Python interpreter path.

Make sure to install and enable these extensions for the best development experience!
