__all__ = ("ExitException", "InvalidConfigurationException")

class ExitException(Exception):
    __slots__ = ("message",)
    def __init__(self, message: str, *args: object) -> None:
        self.message = message
        super().__init__(message, *args)

class InvalidConfigurationException(ExitException):
    def __init__(self, message: str = "Invalid configuration", *args: object) -> None:
        self.message = message
        super().__init__(message, *args)
