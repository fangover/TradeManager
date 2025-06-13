from models.candle import Candle


class CandlestickPatterns:
    @staticmethod
    def is_bullish_engulfing(candles: list[Candle]) -> bool:
        """Bullish Engulfing Pattern (bullish reversal)"""
        if len(candles) < 2:
            return False

        prev, curr = candles[-2], candles[-1]
        return (
            prev.is_bearish
            and curr.is_bullish
            and curr.open < prev.close
            and curr.close > prev.open
        )

    @staticmethod
    def is_bearish_engulfing(candles: list[Candle]) -> bool:
        """Bearish Engulfing Pattern (bearish reversal)"""
        if len(candles) < 2:
            return False

        prev, curr = candles[-2], candles[-1]
        return (
            prev.is_bullish
            and curr.is_bearish
            and curr.open > prev.close
            and curr.close < prev.open
        )

    @staticmethod
    def is_hammer(candles: list[Candle], tolerance: float = 0.05) -> bool:
        """Hammer Pattern (bullish reversal)"""
        if not candles:
            return False

        candle = candles[-1]
        body = candle.body
        upper_shadow = candle.high - max(candle.open, candle.close)
        lower_shadow = min(candle.open, candle.close) - candle.low

        if body == 0:
            return False

        return (
            lower_shadow >= (2 - tolerance) * body
            and upper_shadow <= (0.1 + tolerance) * body
            and candle.is_bullish
        )

    @staticmethod
    def is_shooting_star(candles: list[Candle]) -> bool:
        """Shooting Star Pattern (bearish reversal)"""
        if not candles:
            return False

        candle = candles[-1]
        body = candle.body
        upper_shadow = candle.high - max(candle.open, candle.close)
        lower_shadow = min(candle.open, candle.close) - candle.low

        return (
            upper_shadow >= 2 * body
            and lower_shadow <= body * 0.1
            and candle.is_bearish
        )

    @staticmethod
    def is_doji(candles: list[Candle], max_body_ratio: float = 0.05) -> bool:
        """Doji Pattern (indecision)"""
        if not candles:
            return False

        candle = candles[-1]
        body = candle.body
        full_range = candle.range

        return body <= full_range * max_body_ratio

    @staticmethod
    def is_morning_star(candles: list[Candle]) -> bool:
        """Morning Star Pattern (3-candle bullish reversal)"""
        if len(candles) < 3:
            return False

        first, second, third = candles[-3], candles[-2], candles[-1]
        mid_range = second.high - second.low

        return (
            first.is_bearish
            and second.body < mid_range * 0.5  # Small body
            and third.is_bullish
            and third.close > first.body * 0.5 + first.close  # Closes above midpoint
            and second.low < first.low  # Gap down
            and second.high < first.close  # Confirmed gap
        )

    @staticmethod
    def is_evening_star(candles: list[Candle]) -> bool:
        """Evening Star Pattern (3-candle bearish reversal)"""
        if len(candles) < 3:
            return False

        first, second, third = candles[-3], candles[-2], candles[-1]
        mid_range = second.high - second.low

        return (
            first.is_bullish
            and second.body < mid_range * 0.5  # Small body
            and third.is_bearish
            and third.close < first.body * 0.5 + first.open  # Closes below midpoint
            and second.high > first.high  # Gap up
            and second.low > first.close  # Confirmed gap
        )

    @staticmethod
    def is_hanging_man(candles: list[Candle], tolerance: float = 0.05) -> bool:
        """Hanging Man (bearish reversal at top)"""
        if not candles:
            return False

        candle = candles[-1]
        body = candle.body
        upper_shadow = candle.high - max(candle.open, candle.close)
        lower_shadow = min(candle.open, candle.close) - candle.low

        if body == 0:
            return False

        return (
            lower_shadow >= (2 - tolerance) * body
            and upper_shadow <= (0.1 + tolerance) * body
            and candle.is_bearish
        )

    @staticmethod
    def is_inverted_hammer(candles: list[Candle], tolerance: float = 0.05) -> bool:
        """Inverted Hammer (bullish reversal at bottom)"""
        if not candles:
            return False

        candle = candles[-1]
        body = candle.body
        upper_shadow = candle.high - max(candle.open, candle.close)
        lower_shadow = min(candle.open, candle.close) - candle.low

        if body == 0:
            return False

        return (
            upper_shadow >= (2 - tolerance) * body
            and lower_shadow <= (0.1 + tolerance) * body
            and candle.is_bullish
        )

    @staticmethod
    def is_tweezer_bottom(candles: list[Candle]) -> bool:
        """Tweezer Bottom (bullish reversal)"""
        if len(candles) < 2:
            return False

        first, second = candles[-2], candles[-1]
        return (
            first.is_bearish
            and second.is_bullish
            and abs(first.low - second.low) <= 0.01 * first.low  # 1% tolerance
            and abs(first.close - second.open) <= 0.01 * first.close
        )

    @staticmethod
    def is_tweezer_top(candles: list[Candle]) -> bool:
        """Tweezer Top (bearish reversal)"""
        if len(candles) < 2:
            return False

        first, second = candles[-2], candles[-1]
        return (
            first.is_bullish
            and second.is_bearish
            and abs(first.high - second.high) <= 0.01 * first.high  # 1% tolerance
            and abs(first.close - second.open) <= 0.01 * first.close
        )

    @staticmethod
    def is_three_white_soldiers(candles: list[Candle]) -> bool:
        """Three White Soldiers (strong bullish continuation)"""
        if len(candles) < 3:
            return False

        c1, c2, c3 = candles[-3], candles[-2], candles[-1]
        return (
            c1.is_bullish
            and c2.is_bullish
            and c3.is_bullish
            and c2.open > c1.open
            and c2.close > c1.close
            and c3.open > c2.open
            and c3.close > c2.close
            and (c1.body * 0.5 < c2.body < c1.body * 1.5)
            and (c2.body * 0.5 < c3.body < c2.body * 1.5)
        )

    @staticmethod
    def is_three_black_crows(candles: list[Candle]) -> bool:
        """Three Black Crows (strong bearish continuation)"""
        if len(candles) < 3:
            return False

        c1, c2, c3 = candles[-3], candles[-2], candles[-1]
        return (
            c1.is_bearish
            and c2.is_bearish
            and c3.is_bearish
            and c2.open < c1.open
            and c2.close < c1.close
            and c3.open < c2.open
            and c3.close < c2.close
            and (c1.body * 0.5 < c2.body < c1.body * 1.5)
            and (c2.body * 0.5 < c3.body < c2.body * 1.5)
        )
