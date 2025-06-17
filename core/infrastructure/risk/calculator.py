class RiskCalculator:
    @staticmethod
    def position_size(
        account_balance, stop_loss_pips, risk_pct, pip_value, min_lot_size, max_lot_size
    ):
        if stop_loss_pips == 0 or pip_value == 0:
            raise ValueError("Stop loss pips and pip value must be non-zero.")

        risk_amount = account_balance * risk_pct
        risk_per_lot = stop_loss_pips * pip_value
        size = risk_amount / risk_per_lot
        size = round(max(min_lot_size, min(size, max_lot_size)), 2)
        return float(size)

    @staticmethod
    def stop_loss(price: float, direction: int, sl_distance: float):
        return price - (direction * sl_distance)

    @staticmethod
    def take_profit(price: float, direction: int, tp_distance: float):
        return price + (direction * tp_distance)
