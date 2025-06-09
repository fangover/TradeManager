
# 📈 TradeManager

**TradeManager** is an automated trading system I'm developing on MetaTrader 5. 
As a beginner, I’m exploring my own ideas for managing risk and executing multiple trading strategies in Forex. 
This project is purely for learning and experimentation. 
I’m building something I enjoy, not intended for real trading or financial use

---

## Features

- **Broker Integration** via MetaTrader 5
- **Risk Management** (trailing stop, breakeven, drawdown control, etc.)
- **Multi-Timeframe Strategy Support**
- **Strategies Included**:
  - Breakout Detection & Execution
  - Major Trend Confidence with Quantile Regression
- Candlestick Chart Plotting with Matplotlib
- Modular Event Bus System for loose coupling

---

## TODO

- Add more detailed comments for better understanding.
- Integrate a GUI interface to enhance usability.
- Develop test cases and implement mock functions.


---

Update your config (see `settings.py` or rename `settings_example.py` to `settings.py`) and run:

```bash
python main.py
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
