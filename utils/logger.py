import logging
import os
import sys
from datetime import datetime


class Logger:
    def __init__(self, name='lumora_enrichment', log_dir='logs'):
        self.logger = logging.getLogger(name)

        # Guard against duplicate handlers if Logger() is instantiated more than once
        if self.logger.handlers:
            return

        self.logger.setLevel(logging.DEBUG)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File Handler (only if not on Vercel, as Vercel captures stdout anyway)
        if not os.environ.get('VERCEL'):
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_handler = logging.FileHandler(
                os.path.join(log_dir, f'enrichment_{timestamp}.log')
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def debug(self, message):
        self.logger.debug(message)

    def warning(self, message):
        self.logger.warning(message)


logger = Logger()
