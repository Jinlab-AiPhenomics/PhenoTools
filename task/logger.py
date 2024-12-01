from loguru import logger as loguru_logger
import os


class TaskLogger:
    def __init__(self, task_id=None, log_path=None):
        self.logger = loguru_logger.bind(task_id=task_id)
        self.logger.add(log_path, encoding="utf-8")

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)
