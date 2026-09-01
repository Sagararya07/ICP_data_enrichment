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

        # FIX: the log directory must exist before FileHandler tries to open a
        # file inside it, or this crashes with FileNotFoundError on a fresh checkout.
        os.makedirs(log_dir, exist_ok=True)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # File Handler
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f'enrichment_{timestamp}.log')
        )
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
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
