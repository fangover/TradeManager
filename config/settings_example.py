from dataclasses import dataclass


@dataclass
class Settings:
    # Broker Configuration
    BROKER_LOGIN: int = 123
    BROKER_PASSWORD: str = "123"
    BROKER_SERVER: str = "MetaQuotes-Demo"
    SYMBOL: str = "XAUUSD"
    MAGIC_NUMBER = 666

    # Risk Parameters
    RISK_PER_TRADE: float = 0.05
    MAX_CONSECUTIVE_LOSSES: int = 3
    MAX_DRAWDOWN: float = 0.05
    MAX_POSITIONS: int = 5

    # Strategy Parameters
    SL_RATIO: float = 0.1
    TP_RATIO: float = 0.6
    BREAKOUT_THRESHOLD: float = 0.65

    # Position Management
    TRADE_TIMEOUT: int = 300
    TRAIL_START: float = 22
    TRAIL_DISTANCE: float = 18
    BREAKEVEN_DISTANCE: float = 10

    # System
    HEARTBEAT_INTERVAL: int = 60


config = Settings()
