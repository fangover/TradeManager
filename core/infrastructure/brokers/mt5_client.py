import logging
import time
from datetime import datetime, timedelta, timezone

import MetaTrader5 as mt5

from config.settings import Settings
from core.utilities.logger import logger

from .base import BaseBroker


class MT5Client(BaseBroker):
    def __init__(self, config: Settings):
        self.config = config
        self.connected = False

    def connect(self):
        if not mt5.initialize():  # type: ignore
            logger.error("MT5 initialization failed")
            return False

        if not mt5.login(  # type: ignore
            self.config.BROKER_LOGIN,
            self.config.BROKER_PASSWORD,
            self.config.BROKER_SERVER,
        ):
            logger.error("MT5 login failed")
            return False

        self.connected = True
        return True

    def get_tick(self):
        return mt5.symbol_info_tick(self.config.SYMBOL)  # type: ignore

    def get_candles(self, timeframe, count):
        return mt5.copy_rates_from_pos(  # type: ignore
            self.config.SYMBOL, timeframe, 0, count
        )

    def get_historical_candles(self, timeframe, start_time, end_time):
        symbol = self.config.SYMBOL
        results = []
        chunk_size = timedelta(days=30)
        gmt8 = timezone(timedelta(hours=8))
        current_start = datetime.fromtimestamp(start_time, tz=gmt8)
        end_dt = datetime.fromtimestamp(end_time, tz=gmt8)

        while current_start < end_dt:
            current_end = min(current_start + chunk_size, end_dt)
            rates = mt5.copy_rates_range(  # type: ignore
                symbol,
                timeframe,
                current_start.astimezone(timezone.utc).replace(tzinfo=None),
                current_end.astimezone(timezone.utc).replace(tzinfo=None),
            )

            if rates is not None:
                for rate in rates:
                    utc_time = datetime.utcfromtimestamp(rate["time"]).replace(
                        tzinfo=timezone.utc
                    )
                    gmt8_time = utc_time.astimezone(gmt8)

                    results.append(
                        {
                            "time": gmt8_time.timestamp(),
                            "open": rate["open"],
                            "high": rate["high"],
                            "low": rate["low"],
                            "close": rate["close"],
                            "tick_volume": rate["tick_volume"],
                        }
                    )
            else:
                error = mt5.last_error()  # type: ignore
                logger.error(f"MT5 error ({error})")  # type: ignore
            current_start = current_end + timedelta(seconds=1)
            time.sleep(0.1)

        return results

    def add_order(self, direction, volume, sl, tp, comment="None"):
        trade_type = mt5.ORDER_TYPE_BUY if direction == 1 else mt5.ORDER_TYPE_SELL
        for _ in range(3):

            tick = self.get_tick()
            price = tick.ask if direction == 1 else tick.bid
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.config.SYMBOL,
                "volume": volume,
                "type": trade_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 10,
                "magic": self.config.MAGIC_NUMBER,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)  # type: ignore
            if result:
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    return result
                else:
                    logging.error(f"Error order send: {result.comment}")

                # Only retry if the error is due to a requote or temporary market condition
                if result and result.retcode not in [
                    mt5.TRADE_RETCODE_REQUOTE,
                    mt5.TRADE_RETCODE_PRICE_CHANGED,
                ]:
                    break
            else:
                error = mt5.last_error()  # type: ignore
                self.logger.error(f"Order failed: {error}")  # type: ignore
                return None
                time.sleep(0.5)
        return None

    def modify_position(self, position_id, new_sl, new_tp):
        position = self.get_position_by_id(position_id, self.config.MAGIC_NUMBER)
        if position is not None:
            modify_request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "sl": new_sl,
                "tp": new_tp,
                "position": position.ticket,
            }
            return self.send_order(modify_request)
        return None

    def send_order(self, request):

        error_message = []
        for attempt in range(3):
            result = mt5.order_send(request)  # type: ignore
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return result

            error_message.append(
                f"Attempt {attempt + 1} failed: {result.comment if result else 'No result'}"
            )

            if result and result.retcode not in [
                mt5.TRADE_RETCODE_REQUOTE,
                mt5.TRADE_RETCODE_PRICE_CHANGED,
            ]:
                break
            time.sleep(0.5)

        if error_message is not None:
            logger.error(error_message)
        return None

    def close_position(self, position_id):
        tick = self.get_tick()
        if not tick:
            return False
        position = self.get_position_by_id(position_id, self.config.MAGIC_NUMBER)
        if position is not None:
            price = tick.ask if position.type == mt5.ORDER_TYPE_BUY else tick.bid
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": (
                    mt5.ORDER_TYPE_SELL
                    if position.type == mt5.ORDER_TYPE_BUY
                    else mt5.ORDER_TYPE_BUY
                ),
                "position": position.ticket,
                "price": price,
                "comment": "Risk Close",
            }
            return self.send_order(request)
        return False

    def get_pip_value(self):
        symbol_info = mt5.symbol_info(self.config.SYMBOL)  # type: ignore
        return symbol_info.point

    def get_account_info(self):
        try:
            account_info = mt5.account_info()  # type: ignore
            if account_info:
                return account_info.balance, account_info.equity
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
        return 0, 0

    def get_position_by_id(self, position_id, magic=None):
        if magic is None:
            magic = self.config.MAGIC_NUMBER
        try:
            all_positions = mt5.positions_get(magic=magic)  # type: ignore
            if all_positions is None:
                return None

            for pos in all_positions:
                if pos.ticket == position_id:
                    return pos

            return None
        except:
            return None

    def get_positions(self, symbol=None, magic=None):
        if magic is None:
            magic = self.config.MAGIC_NUMBER
        if symbol is None:
            symbol = self.config.SYMBOL

        try:
            if symbol:
                return mt5.positions_get(symbol=symbol, magic=magic)  # type: ignore
            return mt5.positions_get(magic=magic)  # type: ignore
        except:
            return None

    def has_open_position(self, direction):
        positions = self.get_positions(self.config.SYMBOL, magic=666) or []
        for pos in positions:
            if (direction == 1 and pos.type == mt5.ORDER_TYPE_BUY) or (
                direction == -1 and pos.type == mt5.ORDER_TYPE_SELL
            ):
                return True
        return False

    def get_positions_by_comment(self, comment, symbol=None, magic=None):
        if magic is None:
            magic = self.config.MAGIC_NUMBER
        if symbol is None:
            symbol = self.config.SYMBOL

        try:
            positions = mt5.positions_get(symbol=symbol, magic=magic)  # type: ignore
            if positions is None:
                return []
            return [pos for pos in positions if pos.comment == comment]

        except Exception as e:
            logger.error(f"Error getting positions by comment: {e}")
            return []

    def has_positions_by_comment(self, comment, symbol=None, magic=None):
        positions = self.get_positions_by_comment(comment, symbol, magic)
        return len(positions) > 0
