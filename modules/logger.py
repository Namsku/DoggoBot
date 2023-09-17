import logging
import os


class Logger(logging.Logger):
    def __init__(self, name: str) -> None:
        """
        Initializes a new logger object.

        Parameters
        ----------
        name : str
            The name of the logger.

        Returns
        -------
        None
        """

        super().__init__(name)
        self.setLevel(logging.DEBUG)

        # Create a file handler
        self.create_logger_file()
        file_handler = logging.FileHandler("data/logs/doggobot.log", "w", "utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.addHandler(file_handler)

        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.addHandler(console_handler)

    def create_logger_file(self) -> None:
        """
        Creates a logger file if it doesn't exist.

        Parameters

        ----------
        None

        Returns
        -------
        None
        """
        if not os.path.exists("data/logs"):
            os.makedirs("data/logs")

        if not os.path.exists("data/logs/doggobot.log"):
            open("data/logs/doggobot.log", "w").close()

    def debug(self, message: str) -> None:
        """
        Logs a message with level DEBUG on the root logger.

        Parameters

        ----------

        message : str
            The message to log.

        Returns
        -------
        None
        """
        self.log(logging.DEBUG, message)

    def info(self, message: str) -> None:
        """
        Logs a message with level INFO on the root logger.

        Parameters

        ----------

        message : str
            The message to log.

        Returns
        -------
        None
        """
        self.log(logging.INFO, message)

    def warning(self, message: str) -> None:
        """
        Logs a message with level WARNING on the root logger.

        Parameters

        ----------

        message : str
            The message to log.

        Returns
        -------
        None
        """
        self.log(logging.WARNING, message)

    def error(self, message: str) -> None:
        """
        Logs a message with level ERROR on the root logger.

        Parameters

        ----------

        message : str
            The message to log.

        Returns
        -------
        None
        """
        self.log(logging.ERROR, message)

    def critical(self, message: str) -> None:
        """
        Logs a message with level CRITICAL on the root logger.

        Parameters

        ----------

        message : str
            The message to log.

        Returns
        -------
        None
        """
        self.log(logging.CRITICAL, message)
