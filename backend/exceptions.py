class CryptoBaseError(Exception):
    """Base exception for all crypto-related errors."""
    def __init__(self, message: str, user_message: str = None):
        super().__init__(message)
        self.user_message = user_message or "An unexpected error occurred. Please try again."

class InvalidWorkflowTransitionError(CryptoBaseError):
    """Raised when a trade moves to an illegal state."""
    pass

class DuplicateExecutionError(CryptoBaseError):
    """Raised when a trade attempt is detected as a duplicate."""
    pass

class RiskViolationError(CryptoBaseError):
    """Raised when risk checks fail."""
    pass

class ExchangeUnavailableError(CryptoBaseError):
    """Raised when the exchange API is down or timing out."""
    pass

class InsufficientBalanceError(CryptoBaseError):
    """Raised when wallet balance is too low."""
    pass

class RateLimitExceededError(CryptoBaseError):
    """Raised when user hits API/Trade limits."""
    pass
