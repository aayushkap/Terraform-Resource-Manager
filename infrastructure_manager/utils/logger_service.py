import logging
import os


class Logger:
    _logger = None  # shared singleton

    def __init__(self, file_name: str = None):
        if Logger._logger:
            self.logger = Logger._logger
            return

        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app.log")

        logger = logging.getLogger("AppLogger")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if not logger.handlers:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            formatter = logging.Formatter(
                fmt="[{levelname}] [{filename}]\t{message}", style="{"
            )

            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        Logger._logger = logger
        self.logger = logger

    def get_logger(self):
        return self.logger
