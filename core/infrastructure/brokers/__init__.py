from .mt5_client import MT5Client


class BrokerFactory:
    @staticmethod
    def create(config):
        broker = MT5Client(config)
        if broker.connect():
            return broker
        raise ConnectionError("Failed to connect to broker")
