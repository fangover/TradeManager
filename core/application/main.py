from app import TradeApp

from config.settings import config
from core.utilities.logger import logger

if __name__ == "__main__":
    app = TradeApp(config)
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.exception(f"Fatal error occurred : {e}")
    finally:
        app.shutdown()
