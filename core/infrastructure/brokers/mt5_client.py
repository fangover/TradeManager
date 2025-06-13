import logging
import time

import MetaTrader5 as mt5

from config.settings import Settings

from .base import BaseBroker


class MT5Client(BaseBroker):
    def __init__(self, config: Settings):
        self.config = config
        self.logger = logging.getLogger("mt5")
        self.connected = False

    def connect(self):
        if not mt5.initialize():  # type: ignore
            self.logger.error("MT5 initialization failed")
            return False

        if not mt5.login(  # type: ignore
            self.config.BROKER_LOGIN,
            self.config.BROKER_PASSWORD,
            self.config.BROKER_SERVER,
        ):
            self.logger.error("MT5 login failed")
            return False

        self.connected = True
        return True

    def get_tick(self):
        return mt5.symbol_info_tick(self.config.SYMBOL)  # type: ignore

    def get_candles(self, timeframe, count):
        return mt5.copy_rates_from_pos(  # type: ignore
            self.config.SYMBOL, timeframe, 0, count
        )

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
                logging.error(f"Error order send: Empty result")
                break
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
        for attempt in range(3):
            result = mt5.order_send(request)  # type: ignore
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return result

            self.logger.warning(
                f"Attempt {attempt + 1} failed: {result.comment if result else 'No result'}"
            )

            if result and result.retcode not in [
                mt5.TRADE_RETCODE_REQUOTE,
                mt5.TRADE_RETCODE_PRICE_CHANGED,
            ]:
                break
            time.sleep(0.5)
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
            self.logger.error(f"Failed to get account info: {e}")
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
