import logging
import os
from typing import Optional
import yaml

def setup_logger(
    config_path: Optional[str] = None,
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """Setup logger for the network agent

    Args:
        config_path: Path to config file with logging settings
        level: Default log level if not specified in config
        log_file: Default log file if not specified in config

    Returns:
        Configured logger instance
    """
    # Base configuration
    log_config = {
        "level": level,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": log_file
    }

    # Load config from file if provided
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
                if "logging" in config:
                    log_config.update(config["logging"])
        except Exception as e:
            print(f"Warning: Could not load logging config: {e}")

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_config["level"]),
        format=log_config["format"],
        filename=log_config["file"]
    )

    # Create logger
    logger = logging.getLogger("NetworkAgent")

    # Add console handler if no file specified
    if not log_config["file"]:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(log_config["format"])
        )
        logger.addHandler(console_handler)

    return logger