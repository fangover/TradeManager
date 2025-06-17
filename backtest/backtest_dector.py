import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import MetaTrader5 as mt5

from config.settings import Settings
from core.infrastructure.brokers.mt5_client import MT5Client
from core.infrastructure.candle.manger import CandleManager
from core.strategies.mtc.detector import MajorTrendConfidenceDetector
from core.strategies.scalping_m1 import ScalpingDetector
from models import Candle


class RegisteredDetector:
    """Holds detector instance and trade history for a timeframe."""

    def __init__(self, name, detector, timeframe):
        self.name = name
        self.detector = detector
        self.timeframe = timeframe
        self.open_positions = []
        self.closed_positions = []


class BacktestState:
    """Minimal state wrapper using the real CandleManager."""

    def __init__(self, broker: MT5Client):
        self.broker = broker
        self.candle_manager = CandleManager(broker)

    def get_candles(self, timeframe, count=None):
        return self.candle_manager.get_candles(timeframe, count)

    def calculate_atr(self, timeframe, period=14, smoothing_period=None):
        return self.candle_manager.calculate_atr(timeframe, period, smoothing_period)


class BacktestRunner:
    """Manages registered detectors and executes the backtest."""

    def __init__(
        self,
        broker: MT5Client,
        state: BacktestState,
        config: Settings,
        pip_point: float,
    ):
        self.broker = broker
        self.state = state
        self.config = config
        self.pip_point = pip_point
        self.detectors: list[RegisteredDetector] = []

    def register(self, name: str, detector, timeframe) -> None:
        self.detectors.append(RegisteredDetector(name, detector, timeframe))

    def _check_positions(self, candle: Candle, entry: RegisteredDetector):
        for pos in list(entry.open_positions):
            if pos["direction"] == 1:
                if candle.low <= pos["sl"]:
                    pos["close_time"] = candle.timestamp
                    pos["close_price"] = pos["sl"]
                    pos["profit_pips"] = (
                        (pos["close_price"] - pos["entry"])
                        * pos["direction"]
                        / (self.pip_point * 10)
                    )
                    pos["result"] = "SL"
                    entry.closed_positions.append(pos)
                    entry.open_positions.remove(pos)
                    continue
                if candle.high >= pos["tp"]:
                    pos["close_time"] = candle.timestamp
                    pos["close_price"] = pos["tp"]
                    pos["profit_pips"] = (
                        (pos["close_price"] - pos["entry"])
                        * pos["direction"]
                        / (self.pip_point * 10)
                    )
                    pos["result"] = "TP"
                    entry.closed_positions.append(pos)
                    entry.open_positions.remove(pos)
                    continue
            else:
                if candle.high >= pos["sl"]:
                    pos["close_time"] = candle.timestamp
                    pos["close_price"] = pos["sl"]
                    pos["profit_pips"] = (
                        (pos["close_price"] - pos["entry"])
                        * pos["direction"]
                        / (self.pip_point * 10)
                    )
                    pos["result"] = "SL"
                    entry.closed_positions.append(pos)
                    entry.open_positions.remove(pos)
                    continue
                if candle.low <= pos["tp"]:
                    pos["close_time"] = candle.timestamp
                    pos["close_price"] = pos["tp"]
                    pos["profit_pips"] = (
                        (pos["close_price"] - pos["entry"])
                        * pos["direction"]
                        / (self.pip_point * 10)
                    )
                    pos["result"] = "TP"
                    entry.closed_positions.append(pos)
                    entry.open_positions.remove(pos)
                    continue

    def _open_position(self, entry: RegisteredDetector, candle: Candle, signal: int):
        atr = self.state.calculate_atr(entry.timeframe, 14)
        if atr == 0:
            return

        sl_distance = atr * 1.5
        tp_distance = atr * 3

        entry_price = candle.close
        sl = entry_price - signal * sl_distance
        tp = entry_price + signal * tp_distance
        entry.open_positions.append(
            {
                "direction": signal,
                "entry": entry_price,
                "sl": sl,
                "tp": tp,
                "open_time": candle.timestamp,
            }
        )
        print(
            f"  Open {('LONG' if signal==1 else 'SHORT')} at {entry_price:.2f} SL {sl:.2f} TP {tp:.2f}"
        )

    def run(self, days: int = 1) -> None:
        end = datetime.now()
        start = end - timedelta(days=days)

        for entry in self.detectors:
            tf = entry.timeframe
            candles = self.broker.get_historical_candles(
                tf, start.timestamp(), end.timestamp()
            )
            if not candles:
                print(f"No candles retrieved for {entry.name}")
                continue

            tf_text = self.state.candle_manager.timeframe_text.get(tf, str(tf))
            print(f"\n=== Running {entry.name} on {tf_text} ===")

            for data in candles:
                candle = Candle(
                    timestamp=data["time"],
                    open=data["open"],
                    high=data["high"],
                    low=data["low"],
                    close=data["close"],
                    volume=data["tick_volume"],
                    timeframe=tf,
                )
                self.state.candle_manager.add_candle(candle)

                self._check_positions(candle, entry)

                signal = (
                    entry.detector.detect() if len(entry.open_positions) <= 0 else 0
                )
                if signal in [-1, 1]:
                    date_str = datetime.fromtimestamp(candle.timestamp).strftime(
                        "%Y-%m-%d"
                    )
                    print(f"{date_str}: signal={signal}")
                    self._open_position(entry, candle, signal)

            # Print summary per detector
            print("\nClosed Positions for", entry.name)
            total_pips = 0.0
            for pos in entry.closed_positions:
                close_date = datetime.fromtimestamp(pos["close_time"]).strftime(
                    "%Y-%m-%d"
                )
                profit = pos.get("profit_pips", 0.0)
                total_pips += profit
                print(
                    f"  {close_date} {pos['result']} at {pos['close_price']:.2f} (entry {pos['entry']:.2f}) {profit:.1f} pips"
                )

            print(f"Total P/L for {entry.name}: {total_pips:.1f} pips\n")


def main():
    config = Settings()
    broker = MT5Client(config)

    if not broker.connect():
        print("Failed to connect to MetaTrader 5")
        return

    pip_point = broker.get_pip_value()

    state = BacktestState(broker)
    runner = BacktestRunner(broker, state, config, pip_point)
    runner.register(
        "M1 Scalper", ScalpingDetector(broker, state, config), mt5.TIMEFRAME_M1  # type: ignore
    )

    runner.run(days=100)


if __name__ == "__main__":
    main()
