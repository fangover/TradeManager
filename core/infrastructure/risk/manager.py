from config.settings import Settings
from core.application.state import TradingState
from core.infrastructure.brokers.base import BaseBroker
from core.utilities.event_bus import EventBus
from core.utilities.logger import logger
from models import Position


class RiskManager:
    def __init__(
        self, broker: BaseBroker, state: TradingState, config: Settings, bus: EventBus
    ):
        self.broker = broker
        self.state = state
        self.config = config
        self.bus = bus

    def evaluate(self):
        self.monitor_positions()
        self.circuit_breaker_check()

    def monitor_positions(self):
        """Monitor exisitnig position on MT5 broker."""
        for position in list(self.state.position_manager.open_positions.values()):
            position: Position
            print(
                f"Position #{position.id} | Type: {'BUY' if position.direction == 1 else 'SELL'} | "
                f"Open: {position.entry_price:.2f} | Current: {position.current_price:.2f} | Size: {position.size:.2f} | "
                f"Profit: ${position.unrealized_pnl:.2f} | Pips: {position.unrealized_pnl_pips:.1f}"
            )
            self.check_position_risk(position)

    def check_position_risk(self, position: Position):
        if position.time_out != 0 and position.age > position.time_out:
            self.state.position_manager.close_position(position.id, "Timeout")

        if position.unrealized_pnl_pips > self.config.TRAIL_START:
            self.apply_trailing_stop(position)
        elif position.unrealized_pnl_pips > self.config.BREAKEVEN_DISTANCE:
            self.apply_breakeven(position)

    def apply_breakeven(self, position: Position):
        """Breakeven poistion when pnl reached breakeven distance pips."""
        breakeven_sl = position.entry_price + position.direction * position.pips_point

        # Only update if SL is worse than breakeven
        if (position.direction == 1 and position.stop_loss < breakeven_sl) or (
            position.direction == -1 and position.stop_loss > breakeven_sl
        ):
            self.broker.modify_position(position.id, breakeven_sl, position.take_profit)
            position.update_sl(breakeven_sl)
            logger.info(
                f"Breakeven SL updated for position {position.id}: {breakeven_sl}"
            )

    def apply_trailing_stop(self, position: Position):
        trail_offset = self.config.TRAIL_DISTANCE * position.pips_point
        new_sl = position.current_price - (position.direction * trail_offset)

        if position.stop_loss != 0:
            if (position.direction == 1 and new_sl <= position.stop_loss) or (
                position.direction == -1 and new_sl >= position.stop_loss
            ):
                return

        self.broker.modify_position(position.id, new_sl, position.take_profit)
        position.update_sl(new_sl)
        logger.info(f"Trailing SL updated for position {position.id}: {new_sl}")

    def circuit_breaker_check(self):
        if self.state.account_balance <= 100:
            self.bus.publish("RISK_VIOLATION", "Account balance is zero!")
            return

        if (
            self.state.position_manager.consecutive_losses
            > self.config.MAX_CONSECUTIVE_LOSSES
        ):
            self.bus.publish(
                "RISK_VIOLATION",
                f"{self.state.position_manager.consecutive_losses} consecutive losses",
            )

        drawdown = (
            self.state.account_balance - self.state.account_equity
        ) / self.state.account_balance
        if drawdown > self.config.MAX_DRAWDOWN:
            self.bus.publish(
                "RISK_VIOLATION", f"Drawdown {drawdown*100:.2f}% exceeds limit"
            )
