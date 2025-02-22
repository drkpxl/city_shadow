"""
Centralized logging management for Shadow City Generator.

This module provides a unified logging interface for the entire application,
supporting both console output and debug log collection.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List, Union, Any
from datetime import datetime


class LoggingManager:
    """
    Manages logging configuration and debug message handling.

    This class provides a centralized logging solution with support for:
    - Console output with different log levels
    - Debug log collection
    - File logging (optional)
    - Structured logging formats
    """

    def __init__(
        self,
        debug: bool = False,
        log_file: Optional[Union[str, Path]] = None,
        module_name: str = "",
    ):
        """
        Initialize the logging manager.

        Args:
            debug: Enable debug mode for verbose output
            log_file: Optional path to write logs to file
            module_name: Optional module name for log attribution
        """
        self.debug = debug
        self.debug_log: List[str] = []
        self.module_name = module_name

        # Configure logger
        logger_name = f"shadow_city.{module_name}" if module_name else "shadow_city"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)

        # Prevent duplicate messages
        self.logger.propagate = False

        # Remove any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if debug else logging.INFO)

        # Create formatters
        console_fmt = "%(message)s"
        if debug:
            console_fmt = "%(levelname)s: %(message)s"
        if module_name:
            console_fmt = f"[{module_name}] {console_fmt}"

        console_formatter = logging.Formatter(console_fmt)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler if requested
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_fmt = "%(asctime)s - %(levelname)s - %(message)s"
            if module_name:
                file_fmt = f"%(asctime)s - {module_name} - %(levelname)s - %(message)s"
            file_formatter = logging.Formatter(file_fmt)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def _format_message(self, *args: Any, separator: str = " ") -> str:
        """
        Format message parts into a single string.

        Args:
            *args: Message parts to combine
            separator: String used to join the message parts

        Returns:
            Formatted message string
        """
        return separator.join(str(arg) for arg in args)

    def debug(self, *args: Any, separator: str = " ") -> None:
        """
        Log a debug message and store it in the debug log if debug mode is enabled.

        Args:
            *args: Objects to log (will be converted to strings)
            separator: String used to join the message parts
        """
        if not self.debug:
            return

        message = self._format_message(*args, separator=separator)
        self.logger.debug(message)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.debug_log.append(f"{timestamp} - DEBUG - {message}")

    def info(self, *args: Any, separator: str = " ") -> None:
        """
        Log an info message.

        Args:
            *args: Objects to log (will be converted to strings)
            separator: String used to join the message parts
        """
        message = self._format_message(*args, separator=separator)
        self.logger.info(message)

    def warning(self, *args: Any, separator: str = " ") -> None:
        """
        Log a warning message.

        Args:
            *args: Objects to log (will be converted to strings)
            separator: String used to join the message parts
        """
        message = self._format_message(*args, separator=separator)
        self.logger.warning(message)

    def error(self, *args: Any, separator: str = " ") -> None:
        """
        Log an error message.

        Args:
            *args: Objects to log (will be converted to strings)
            separator: String used to join the message parts
        """
        message = self._format_message(*args, separator=separator)
        self.logger.error(message)

    def get_debug_log(self) -> List[str]:
        """
        Return the collected debug log messages.

        Returns:
            List of debug messages with timestamps
        """
        return self.debug_log

    def write_debug_log(self, filepath: Union[str, Path]) -> None:
        """
        Write the debug log to a file.

        Args:
            filepath: Path to write the debug log
        """
        if not self.debug_log:
            return

        with open(filepath, "w") as f:
            f.write("\n".join(self.debug_log))
