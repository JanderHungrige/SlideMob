import logging
from typing import Optional
import os

class TranslationLogger:
    def __init__(self, log_file: Optional[str] = None):
        self.logger = logging.getLogger('translation')
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
            
    def info(self, message: str):
        self.logger.info(message)
        
    def error(self, message: str):
        self.logger.error(message)
        
    def debug(self, message: str):
        self.logger.debug(message) 