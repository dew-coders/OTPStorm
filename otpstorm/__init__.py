"""
OTPStorm - OTP Spam Tool

A prank application that floods a target phone number with OTP verification
messages using multiple service provider APIs.

This tool is intended for educational purposes only.
Use at your own risk and only on numbers you own or have permission to test.
"""

__version__ = "2.0.0"
__author__ = "Dew Coders"
__license__ = "Educational Use Only"
__description__ = "Multi-provider OTP flooding tool"

from otpstorm.logger import setup_logger, get_logger as _get_logger

_logger = _get_logger(__name__)
_logger.debug("OTPStorm v%s initialized", __version__)
