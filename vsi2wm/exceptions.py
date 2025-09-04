"""Custom exceptions for VSI to WireMock converter."""


class CLIError(Exception):
    """Custom exception for CLI errors."""
    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


class ConversionError(Exception):
    """Custom exception for conversion errors."""
    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)
