import os
import sys
import unittest
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.infrastructure.candle import CandlestickPatterns, plotter
from models import Candle


def to_unix(date_str):
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())


class TestCandlestickPatterns(unittest.TestCase):

    def test_bullish_engulfing(self):
        candle1 = Candle(
            timestamp=to_unix("2023-01-01"),
            open=100,
            high=105,
            low=95,
            close=98,
            volume=1000,
            timeframe="1h",
        )
        candle2 = Candle(
            timestamp=to_unix("2023-01-02"),
            open=97,
            high=108,
            low=96,
            close=102,
            volume=1500,
            timeframe="1h",
        )
        candles = [candle1, candle2]
        self.assertTrue(CandlestickPatterns.is_bullish_engulfing(candles))
        plotter.plot_candles(candles, "Bullish Engulfing")

    def test_bearish_engulfing(self):
        candle1 = Candle(
            timestamp=to_unix("2023-01-08"),
            open=80,
            high=85,
            low=79,
            close=82,
            volume=1100,
            timeframe="1h",
        )
        candle2 = Candle(
            timestamp=to_unix("2023-01-09"),
            open=83,
            high=84,
            low=78,
            close=79,
            volume=1300,
            timeframe="1h",
        )
        candles = [candle1, candle2]
        self.assertTrue(CandlestickPatterns.is_bearish_engulfing(candles))
        plotter.plot_candles(candles, "Bearish Engulfing")

    def test_hammer(self):
        # Invalid hammer (upper shadow too big)
        candle = Candle(
            timestamp=to_unix("2023-01-03"),
            open=50,
            high=50.5,
            low=45,
            close=50.2,
            volume=1200,
            timeframe="1h",
        )
        self.assertFalse(CandlestickPatterns.is_hammer([candle]))

        # Valid hammer
        candle = Candle(
            timestamp=to_unix("2023-01-03"),
            open=50,
            high=50.04,
            low=45,
            close=50.05,
            volume=1200,
            timeframe="1h",
        )
        self.assertTrue(CandlestickPatterns.is_hammer([candle]))
        plotter.plot_candles([candle], "Hammer")

    def test_morning_star(self):
        candle1 = Candle(
            timestamp=to_unix("2023-01-04"),
            open=100,
            high=102,
            low=95,
            close=96,
            volume=1000,
            timeframe="1h",
        )
        candle2 = Candle(
            timestamp=to_unix("2023-01-05"),
            open=94,
            high=95,
            low=93,
            close=94.5,
            volume=800,
            timeframe="1h",
        )
        candle3 = Candle(
            timestamp=to_unix("2023-01-06"),
            open=95,
            high=104,
            low=94,
            close=102,
            volume=1500,
            timeframe="1h",
        )

        candles = [candle1, candle2, candle3]
        self.assertTrue(CandlestickPatterns.is_morning_star(candles))
        plotter.plot_candles(candles, "Morning Star")

    def test_doji(self):
        candle = Candle(
            timestamp=to_unix("2023-01-07"),
            open=75,
            high=76,
            low=74,
            close=75.01,
            volume=900,
            timeframe="1h",
        )
        self.assertTrue(CandlestickPatterns.is_doji([candle]))
        plotter.plot_candles([candle], "Doji")

    def test_hanging_man(self):
        # Valid hanging man
        candle = Candle(
            timestamp=to_unix("2023-01-18"),
            open=110,
            high=109.05,
            low=105,
            close=109,
            volume=1200,
            timeframe="1h",
        )
        plotter.plot_candles([candle], "Hanging Man")
        self.assertTrue(CandlestickPatterns.is_hanging_man([candle]))

    def test_inverted_hammer(self):
        # Valid inverted hammer
        candle = Candle(
            timestamp=to_unix("2023-01-19"),
            open=50,
            high=55,
            low=50.3,
            close=50.5,
            volume=1100,
            timeframe="1h",
        )
        self.assertTrue(CandlestickPatterns.is_inverted_hammer([candle]))
        plotter.plot_candles([candle], "Inverted Hammer")

    def test_tweezer_bottom(self):
        # Valid tweezer bottom
        candle1 = Candle(
            timestamp=to_unix("2023-01-22"),
            open=90,
            high=92,
            low=85,
            close=87,
            volume=1000,
            timeframe="1h",
        )
        candle2 = Candle(
            timestamp=to_unix("2023-01-23"),
            open=87,
            high=90,
            low=85,
            close=89,
            volume=1100,
            timeframe="1h",
        )
        candles = [candle1, candle2]
        self.assertTrue(CandlestickPatterns.is_tweezer_bottom(candles))
        plotter.plot_candles(candles, "Tweezer Bottom")

    def test_tweezer_top(self):
        # Valid tweezer top
        candle1 = Candle(
            timestamp=to_unix("2023-01-24"),
            open=95,
            high=100,
            low=94,
            close=97,
            volume=1200,
            timeframe="1h",
        )
        candle2 = Candle(
            timestamp=to_unix("2023-01-25"),
            open=97,
            high=100,
            low=93,
            close=95,
            volume=1300,
            timeframe="1h",
        )
        candles = [candle1, candle2]
        self.assertTrue(CandlestickPatterns.is_tweezer_top(candles))
        plotter.plot_candles(candles, "Tweezer Top")

    def test_three_white_soldiers(self):
        # Valid three white soldiers
        candle1 = Candle(
            timestamp=to_unix("2023-01-26"),
            open=50,
            high=53,
            low=49,
            close=52,
            volume=1000,
            timeframe="1h",
        )
        candle2 = Candle(
            timestamp=to_unix("2023-01-27"),
            open=52.5,
            high=55,
            low=51.5,
            close=54.5,
            volume=1100,
            timeframe="1h",
        )
        candle3 = Candle(
            timestamp=to_unix("2023-01-28"),
            open=54.5,
            high=58,
            low=54,
            close=57,
            volume=1200,
            timeframe="1h",
        )
        candles = [candle1, candle2, candle3]
        self.assertTrue(CandlestickPatterns.is_three_white_soldiers(candles))
        plotter.plot_candles(candles, "Three White Soldiers")

    def test_three_black_crows(self):
        # Valid three black crows
        candle1 = Candle(
            timestamp=to_unix("2023-01-29"),
            open=60,
            high=61,
            low=57,
            close=58,
            volume=1000,
            timeframe="1h",
        )
        candle2 = Candle(
            timestamp=to_unix("2023-01-30"),
            open=57.5,
            high=58,
            low=55,
            close=55.5,
            volume=1100,
            timeframe="1h",
        )
        candle3 = Candle(
            timestamp=to_unix("2023-01-31"),
            open=55,
            high=56,
            low=52,
            close=53,
            volume=1200,
            timeframe="1h",
        )
        candles = [candle1, candle2, candle3]
        self.assertTrue(CandlestickPatterns.is_three_black_crows(candles))
        plotter.plot_candles(candles, "Three Black Crows")

    def test_invalid_patterns(self):
        # Test invalid patterns that shouldn't trigger detection
        candle = Candle(
            timestamp=to_unix("2023-02-01"),
            open=100,
            high=105,
            low=100,
            close=105,
            volume=1000,
            timeframe="1h",
        )
        # Should not be a hammer
        self.assertFalse(CandlestickPatterns.is_hammer([candle]))

        # Should not be a doji
        self.assertFalse(CandlestickPatterns.is_doji([candle]))

        # Should not be a hanging man
        self.assertFalse(CandlestickPatterns.is_hanging_man([candle]))

        # Single candle shouldn't be any pattern that requires multiple candles
        self.assertFalse(CandlestickPatterns.is_bullish_engulfing([candle]))
        self.assertFalse(CandlestickPatterns.is_morning_star([candle]))
        self.assertFalse(CandlestickPatterns.is_three_white_soldiers([candle]))


if __name__ == "__main__":
    unittest.main()
