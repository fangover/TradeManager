class RiskCalculator:
    @staticmethod
    def position_size(account_balance, stop_loss_pips, risk_pct, pip_value):
        risk_amount = account_balance * risk_pct
        risk_per_share = stop_loss_pips * pip_value
        return risk_amount / risk_per_share
