import logging

class Logger(logging.Logger):
    def __init__(self, name: str) -> None:
        '''
        Initializes a new logger object.
        
        Parameters
        ----------
        name : str
            The name of the logger.

        Returns
        -------
        None        
        '''

        super().__init__(name)
        self.setLevel(logging.DEBUG)

        # Create a file handler
        file_handler = logging.FileHandler('data/logs/doggobot.log', 'w', 'utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.addHandler(file_handler)

        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.addHandler(console_handler)

    def debug(self, message: str) -> None:
        '''
        Logs a message with level DEBUG on the root logger.
        
        Parameters
        
        ----------
        
        message : str
            The message to log.
            
        Returns
        -------
        None
        '''
        self.log(logging.DEBUG, message)

    def info(self, message: str) -> None:
        '''
        Logs a message with level INFO on the root logger.
        
        Parameters
        
        ----------
        
        message : str
            The message to log.
            
        Returns
        -------
        None
        '''
        self.log(logging.INFO, message)

    def warning(self, message: str) -> None:
        '''
        Logs a message with level WARNING on the root logger.
        
        Parameters
        
        ----------
        
        message : str
            The message to log.
            
        Returns
        -------
        None
        '''
        self.log(logging.WARNING, message)

    def error(self, message: str) -> None:
        '''
        Logs a message with level ERROR on the root logger.
        
        Parameters
        
        ----------
        
        message : str
            The message to log.
            
        Returns
        -------
        None
        '''
        self.log(logging.ERROR, message)

    def critical(self, message: str) -> None:
        '''
        Logs a message with level CRITICAL on the root logger.
        
        Parameters
        
        ----------
        
        message : str
            The message to log.
            
        Returns
        -------
        None
        '''
        self.log(logging.CRITICAL, message)