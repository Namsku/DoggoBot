from modules.logger import Logger

from json import load, dump
from os import getenv
from re import match

logger = Logger(__name__)

regex = {
    "bot_name": r"^[a-zA-Z0-9_]{4,25}$",
    "streamer_channel": r"^[a-zA-Z0-9_]{4,25}$",
    "prefix": r"[?!@#$%^&*a-zA-Z]{1,2}",
    "coin_name": r"[a-zA-Z0-9][\w]{2,24}",
    "default_income": r"[0-9]{1,100}",
    "default_timeout": r"[0-9]{1,100}",
}


class Config:
    content = None

    def __init__(self) -> None:
        self.load_config()
        self.check_config()

    def load_config(self) -> None:
        """
        Creates a configuration file.

        Parameters
        ----------
        None

        Returns
        -------
        config : dict
            The configuration dictionary.
        """
        try:
            with open("data/" + getenv("CONFIG_FILENAME"), "r") as my_config:
                self.content = load(my_config)
        except Exception as e:
            logger.error(f"Error creating config file: {e}")
            exit(1)

        logger.debug("Config file loaded successfully.")

    def save_config(self, config: dict) -> None:
        """
        Saves the configuration file.

        Parameters
        ----------
        config : dict
            The configuration dictionary.

        Returns
        -------
        None
        """
        try:
            with open("data/" + getenv("CONFIG_FILENAME"), "w") as my_config:
                dump(config, my_config)

            self.content = {
                "bot_name": config["bot_name"],
                "streamer_channel": config["streamer_channel"],
                "prefix": config["prefix"],
                "coin_name": config["coin_name"],
                "default_income": config["default_income"],
                "default_timeout": config["default_timeout"],
            }

        except Exception as e:
            logger.error(f"Error saving config file: {e}")
            exit(1)

        logger.debug("Config file saved successfully.")

    def check_config(self):
        for key, value in self.content.items():
            if value == "":
                logger.error(f"Config key {key} is empty.")
                exit(1)

            self._regex_match(regex[key], str(value))

        logger.debug("Config file is correct, Bot creation is now possible.")

    def _regex_match(self, regex: str, string: str) -> None:
        """
        Checks if a string matches a regular expression.

        Parameters
        ----------
        regex : str
            The regular expression to match.
        string : str
            The string to check.

        Returns
        -------
        bool
            True if the string matches the regular expression, False otherwise.
        """

        if not match(regex, string):
            logger.error(f"String {string} does not match regex {regex}.")
            exit(1)
