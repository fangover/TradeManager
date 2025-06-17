from core.infrastructure.brokers.base import BaseBroker
from core.utilities.event_bus import EventBus
from models import Position


class PositionManager:
    def __init__(self, broker: BaseBroker, bus: EventBus):
        self.broker = broker
        self.bus = bus
        self.open_positions = {}
        self.position_history = []
        self.consecutive_losses = 0
        self.session_volatility = 0

    def update_price(self, tick):
        for position in self.open_positions.values():
            position: Position
            position.update_mark_price(
                tick.bid if position.direction == 1 else tick.ask
            )
            position.pip_point = self.broker.get_pip_value()

    def sync_positions(self):
        current_ids = set()
        positions = self.broker.get_positions()
        if positions:
            for pos in positions:
                pos_id = pos.ticket
                current_ids.add(pos_id)

                if pos_id not in self.open_positions:
                    self.add_position(
                        Position(
                            id=pos_id,
                            symbol=pos.symbol,
                            direction=1 if pos.type == 0 else -1,
                            entry_price=pos.price_open,
                            stop_loss=pos.sl,
                            take_profit=pos.tp,
                            size=pos.volume,
                            pip_point=self.broker.get_pip_value(),
                            time_out=0,
                            comment=pos.comment,
                        )
                    )

        existing_ids = set(self.open_positions.keys())
        closed_ids = existing_ids - current_ids
        for pos_id in closed_ids:
            if pos_id in self.open_positions:
                closed_pos: Position = self.open_positions.pop(pos_id)
                closed_pos.close("Closed externally")
                self.bus.publish("LOG_POSITION", closed_pos)
                self.position_history.append(closed_pos)

    def add_position(self, position: Position):
        self.open_positions[position.id] = position
        self.bus.publish("LOG_POSITION", position)

    def close_position(self, position_id, reason):
        if self.broker.close_position(position_id):
            position: Position = self.open_positions.pop(position_id)
            position.close(reason)
            self.bus.publish("LOG_POSITION", position)
            self.position_history.append(position)

            if position.unrealized_pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
