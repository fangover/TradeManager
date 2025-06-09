from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from matplotlib.dates import DateFormatter


class CandlePlotter:
    def __init__(self):
        plt.style.use("dark_background")

    def plot_candles(self, candles, title="Candlestick Chart", show_volume=False):
        if not candles:
            print("No candles to plot")
            return

        self.fig, self.ax = plt.subplots(figsize=(12, 7))
        self.ax2 = self.ax.twinx()  # Volume axis
        self.ax2.set_ylabel("Volume", color="gray")
        self.ax2.tick_params(axis="y", colors="gray")

        df = pd.DataFrame(
            [
                {
                    "timestamp": datetime.fromtimestamp(candle.timestamp),
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                    "bullish": candle.is_bullish,
                }
                for candle in candles
            ]
        )

        df.set_index("timestamp", inplace=True)
        self._plot_candlesticks(df)
        if show_volume:
            self._plot_volume(df)

        self.ax.set_title(title, fontsize=16, pad=20)
        self.ax.xaxis.set_major_formatter(DateFormatter("%m-%d %H:%M"))
        self.ax.xaxis.set_major_locator(mticker.MaxNLocator(10))
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def _plot_candlesticks(self, df):
        self.ax.vlines(df.index, df["low"], df["high"], color="dimgray", linewidth=0.5)

        bull_df = df[df["bullish"]]
        self.ax.vlines(
            bull_df.index,
            bull_df["open"],
            bull_df["close"],
            color="limegreen",
            linewidth=3,
        )

        bear_df = df[~df["bullish"]]
        self.ax.vlines(
            bear_df.index,
            bear_df["open"],
            bear_df["close"],
            color="orangered",
            linewidth=3,
        )

        df["MA20"] = df["close"].rolling(20).mean()
        df["MA50"] = df["close"].rolling(50).mean()
        self.ax.plot(df.index, df["MA20"], "cyan", label="20-period MA", alpha=0.7)
        self.ax.plot(df.index, df["MA50"], "magenta", label="50-period MA", alpha=0.7)
        self.ax.legend(loc="upper left")

    def _plot_volume(self, df):
        colors = ["limegreen" if bull else "orangered" for bull in df["bullish"]]
        self.ax2.bar(df.index, df["volume"], color=colors, alpha=0.3, width=0.002)
        max_vol = df["volume"].max()
        self.ax2.set_ylim(0, max_vol * 3)

    def save_plot(self, filename="candle_chart.png"):
        self.fig.savefig(filename, dpi=200, bbox_inches="tight")
        print(f"Chart saved as {filename}")


plotter = CandlePlotter()
