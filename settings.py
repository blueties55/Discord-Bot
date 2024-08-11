import os
import logging
from logging.config import dictConfig
import configparser

# Function to read settings from settings.txt
def read_settings(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    
    settings = {}
    
    if 'DEFAULT' in config:
        for key, value in config['DEFAULT'].items():
            key = key.strip()  # Remove any extra spaces
            value = value.strip()  # Remove any extra spaces
            settings[key] = value
            
    return settings

# Read the settings from settings.txt
settings = read_settings('settings.txt')
# Fetch the necessary settings
DISCORD_API_TOKEN = settings.get("discord_api_token")  # Updated key name
COMMAND_PREFIX = settings.get("command_prefix")
DM_RESPONSE = settings.get("dm_response")
OWNER_ROLE = settings.get("owner_role")

# Log directory setup
log_dir = './logs'

# Create log directory if it doesn't exist
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)-10s - %(asctime)s - %(module)-15s : %(message)s"
        },
        "standard": {"format": "%(levelname)-10s - %(name)-15s : %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "console2": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(log_dir, "infos.log"),
            "mode": "w",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "bot": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "discord": {
            "handlers": ["console2", "file"],
            "level": "INFO",
            "propagate": False},
    },
}

# Apply the logging configuration
dictConfig(LOGGING_CONFIG)
