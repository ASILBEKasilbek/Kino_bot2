import logging
from datetime import datetime

class Logger:
    def __init__(self):
        logging.basicConfig(
            filename=f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger()

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)