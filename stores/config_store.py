import json
from pydantic import BaseModel
from fastapi import Path

import settings


class Config(BaseModel):
    interval: int = Path(..., title="Interval", description="Interval in seconds", ge=1, le=10000)
    limit: int = Path(..., title="Limit", description="Number of requests allowed in the interval", ge=1)


class ConfigStore:
    """
    Configuration model for rate limiter.
    Contains interval (in seconds) and limit (number of allowed requests).
    """

    def __init__(self, file_path="config.json"):
        """
        A class to handle reading and writing configuration data to a JSON file.
        """
        self.file_path = file_path

    def set_config(self, config: Config):
        """
        Initializes the ConfigStore object with the provided file path.
        """
        config_dict = dict(config)
        with open(self.file_path, "w") as f:
            json.dump(config_dict, f)

    def get_config(self):
        """
        Retrieve and load the configuration from the JSON file.
        :return: Config object with the loaded settings.
        """
        with open(self.file_path, "r") as f:
            config_dict = json.load(f)
        return Config(**config_dict)


class InMemConfigStore:
    """
    An In-Memory configuration store for the rate limiter to be used for testing.
    """
    def __init__(self):
        # Default configuration
        self.config = Config(interval=60, limit=100)

    def set_config(self, config: Config):
        self.config = config

    def get_config(self):
        return self.config


if settings.STORAGE_TYPE == "in_memory":
    config_store = InMemConfigStore()
else:
    config_store = ConfigStore()
