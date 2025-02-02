import logging
import inspect

class Logger: # pragma: no cover
    __logger = logging.getLogger("TestCaseRunner")
    __logger.setLevel(logging.WARNING)
    __handler = logging.StreamHandler()
    __handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    __logger.addHandler(__handler)

    def __new__(cls, *args, **kwargs):
        raise TypeError(f"This class cannot be instantiated")

    @classmethod
    def enable_debug_mode(cls) -> None:
        cls.__logger.setLevel(logging.DEBUG)
    
    @classmethod
    def disable_debug_mode(cls) -> None:
        cls.__logger.setLevel(logging.WARNING)

    @classmethod
    def warning(cls, msg: str) -> None:
        cls.__logger.warning(msg)

    @classmethod
    def info(cls, msg: str) -> None:
        cls.__logger.info(msg)

    @classmethod
    def debug(cls, msg: str) -> None:
        cls.__logger.debug(msg)

def call_logger(func):
    class_name = inspect.stack()[1].function
    def wrapper(*args, **kwargs):
        Logger.debug(f"{class_name}: Calling {func.__name__}")
        result = func(*args, **kwargs)
        Logger.debug(f"{class_name}: {func.__name__} returned {result}")
        return result
    return wrapper
