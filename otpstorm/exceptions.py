"""
Custom exceptions for OTPStorm.
"""


class OTPStormError(Exception):
    """Base exception for all OTPStorm errors."""


class ProviderError(OTPStormError):
    """Raised when a provider fails to send an OTP."""
    def __init__(self, provider_name: str, message: str, status_code: int = None):
        self.provider_name = provider_name
        self.status_code = status_code
        super().__init__(f"[{provider_name}] {message}" + (f" (HTTP {status_code})" if status_code else ""))


class RateLimitError(ProviderError):
    """Raised when a provider rate-limits the request."""


class ConfigurationError(OTPStormError):
    """Raised when there is a configuration problem."""


class PhoneNumberError(OTPStormError):
    """Raised when the phone number is invalid."""


class NetworkError(OTPStormError):
    """Raised on network connectivity issues."""
