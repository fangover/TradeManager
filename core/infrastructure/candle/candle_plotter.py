import os
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from matplotlib.dates import DateFormatter
from matplotlib.patches import Rectangle

from models import Candle


class CandlePlotter:
    def __init__(self, title="Candlestick Chart", show_volume=False, dark_theme=True):
        self.title = title
        self.show_volume = show_volume
        if dark_theme:
            plt.style.use("dark_background")

        self.h_lines = []
        self.v_lines = []
        self.boxes = []
        self._init_figure()

    def _init_figure(self):
        self.fig, self.ax = plt.subplots(figsize=(12, 7))
        self.ax2 = self.ax.twinx()
        self.ax2.set_ylabel("Volume", color="gray")
        self.ax2.tick_params(axis="y", colors="gray")

    def add_horizontal_line(self, price, **kwargs):
        self.h_lines.append(
            (price, {"color": "white", "linestyle": "--", "alpha": 0.7, **kwargs})
        )
        return self

    def add_vertical_line(self, timestamp, **kwargs):
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)
        self.v_lines.append(
            (timestamp, {"color": "cyan", "linestyle": "-", "alpha": 0.7, **kwargs})
        )
        return self

    def add_box(self, x_start, x_end, y_low, y_high, **kwargs):
        if isinstance(x_start, (int, float)):
            x_start = datetime.fromtimestamp(x_start)
        if isinstance(x_end, (int, float)):
            x_end = datetime.fromtimestamp(x_end)
        self.boxes.append(
            (
                x_start,
                x_end,
                y_low,
                y_high,
                {"facecolor": "grey", "edgecolor": "none", "alpha": 0.3, **kwargs},
            )
        )
        return self

    def plot(self, candles: list[Candle], show=True):
        if not candles:
            raise ValueError("No candles provided for plotting.")

        df = self._to_dataframe(candles)
        self._plot_candles(df)

        if self.show_volume:
            self._plot_volume(df)

        self._plot_annotations()
        self._style_plot()

        if show:
            plt.show()

        self._clear_annotations()

    def plot_and_save(self, candles: list[Candle], filename="candle_chart.png"):
        self.plot(candles, show=False)
        self.save(filename)
        plt.close()

    def save(self, filename="candle_chart.png"):
        output_dir = "out/figure/"
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, os.path.basename(filename))
        self.fig.savefig(full_path, dpi=200, bbox_inches="tight")
        print(f"Chart saved to {full_path}")

    def _to_dataframe(self, candles: list[Candle]):
        return pd.DataFrame(
            [
                {
                    "timestamp": datetime.fromtimestamp(c.timestamp),
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                    "bullish": c.is_bullish,
                }
                for c in candles
            ]
        ).set_index("timestamp")

    def _plot_candles(self, df):
        self.ax.vlines(df.index, df["low"], df["high"], color="dimgray", linewidth=0.5)

        bullish = df[df["bullish"]]
        bearish = df[~df["bullish"]]
        self.ax.vlines(
            bullish.index,
            bullish["open"],
            bullish["close"],
            color="limegreen",
            linewidth=3,
        )
        self.ax.vlines(
            bearish.index,
            bearish["open"],
            bearish["close"],
            color="orangered",
            linewidth=3,
        )

    def _plot_volume(self, df):
        colors = ["limegreen" if bull else "orangered" for bull in df["bullish"]]
        self.ax2.bar(df.index, df["volume"], color=colors, alpha=0.3, width=0.002)
        self.ax2.set_ylim(0, df["volume"].max() * 3)

    def _plot_annotations(self):
        for price, style in self.h_lines:
            self.ax.axhline(price, **style)

        for ts, style in self.v_lines:
            self.ax.axvline(ts, **style)

        for x_start, x_end, y_low, y_high, style in self.boxes:
            width = x_end - x_start
            rect = Rectangle((x_start, y_low), width, y_high - y_low, **style)
            self.ax.add_patch(rect)

    def _style_plot(self):
        self.ax.set_title(self.title, fontsize=16, pad=20)
        self.ax.xaxis.set_major_formatter(DateFormatter("%m-%d %H:%M"))
        self.ax.xaxis.set_major_locator(mticker.MaxNLocator(10))
        plt.xticks(rotation=45)
        plt.tight_layout()

    def _clear_annotations(self):
        self.h_lines.clear()
        self.v_lines.clear()
        self.boxes.clear()
