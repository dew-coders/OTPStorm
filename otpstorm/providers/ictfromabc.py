"""
Provider for ictfromabc.com OTP API.

Endpoint: POST https://ictfromabc.com/api/request-otp-v2/{phone}
Source: User-provided curl command
"""

import json
from typing import Dict, Any

from otpstorm.providers.base import BaseProvider
from otpstorm.providers.registry import register_provider


@register_provider
class IctfromabcProvider(BaseProvider):
    """Send OTP via ictfromabc.com API."""

    name = "ictfromabc"
    description = "ICT From ABC OTP API (Bangladesh)"
    max_retries = 2
    request_timeout = 15

    def send(self, nomor: str, b: str, c: str) -> Dict[str, Any]:
        """
        Send OTP request to ictfromabc.com.

        Uses the exact headers from the provided curl command.
        The phone number is appended directly to the URL path.

        Args:
            nomor: Full phone number with leading 0 (e.g., 0701515602).
            b: Phone number without leading 0.
            c: Phone number with country code.

        Returns:
            Result dictionary.
        """
        # Use the phone number as provided (nomor format: 0XXXXXXXXX)
        # The original curl uses the full number including leading 0
        phone = nomor  # e.g., 0701515602

        url = f"https://ictfromabc.com/api/request-otp-v2/{phone}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) "
                "Gecko/20100101 Firefox/128.0"
            ),
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://www.ictfromabc.com/",
            "Content-Type": "application/json",
            "Origin": "https://www.ictfromabc.com",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Priority": "u=0",
            "TE": "trailers",
        }

        try:
            response = self._make_request(
                method="POST",
                url=url,
                headers=headers,
                data=None,  # --data-raw null
            )

            # Try to parse JSON response for a clearer message
            message = f"HTTP {response.status_code}"
            try:
                resp_data = response.json()
                message = json.dumps(resp_data, ensure_ascii=False)[:150]
            except (json.JSONDecodeError, ValueError):
                if response.text:
                    message = self._truncate(response.text)

            success = response.status_code < 500  # Accept 2xx/4xx as "sent"

            return {
                "success": success,
                "status_code": response.status_code,
                "message": message,
                "response_text": self._truncate(response.text),
            }

        except Exception as e:
            return {
                "success": False,
                "status_code": None,
                "message": str(e),
                "response_text": None,
            }
