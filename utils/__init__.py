import logging

class TokenException(Exception):
    pass

class Logger:
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    @staticmethod
    def warn(message: str) -> None:
        logging.warning(message)

    @staticmethod
    def info(message: str) -> None:
        logging.info(message)
    
    @staticmethod
    def error(message: str) -> None:
        logging.error(message)