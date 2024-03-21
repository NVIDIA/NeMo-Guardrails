"""Colang error types."""


class ColangParsingError(Exception):
    """Raised when there is invalid Colang syntax detected."""


class ColangSyntaxError(Exception):
    """Raised when there is invalid Colang syntax detected."""


class ColangValueError(Exception):
    """Raised when there is an invalid value detected in a Colang expression."""


class ColangRuntimeError(Exception):
    """Raised when there is a Colang related runtime exception."""


class LlmResponseError(Exception):
    """Raised when there is an issue with the lmm response."""
