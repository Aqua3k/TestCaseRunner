import logging

class RunnerLogger:
    # pragma: no cover
    def __init__(self, name: str) -> None:
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.WARNING)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def enable_debug_mode(self) -> None:
        self.logger.setLevel(logging.DEBUG)
    
    def disable_debug_mode(self) -> None:
        self.logger.setLevel(logging.WARNING)

    def function_tracer(self, func):
        def wrapper(*args, **kwargs):
            self.logger.debug(f"{self.name}: Calling {func.__name__}")
            result = func(*args, **kwargs)
            self.logger.debug(f"{self.name}: {func.__name__} returned {result}")
            return result
        return wrapper

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def debug(self, msg: str) -> None:
        self.logger.debug(msg)
