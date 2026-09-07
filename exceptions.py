"""Custom exceptions for map parsing errors."""


class MapParsingError(Exception):
    """Exception raised when map file parsing fails."""

    def __init__(self, message: str, line_number: int = 0) -> None:
        """Initialize MapParsingError.

        Args:
            message: Explanation of the error cause.
            line_number: Line number where error occurred (1-indexed).
        """
        self.line_number: int = line_number
        self.message: str = message
        if line_number > 0:
            super().__init__(f"Line {line_number}: {message}")
        else:
            super().__init__(message)
