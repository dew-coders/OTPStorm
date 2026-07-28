"""
Provider for dmeducation.lk OTP API (Sri Lanka).

Endpoint: POST https://dmeducation.lk/api/auth/otp/request
Source: User-provided curl command
"""

import json
from typing import Dict, Any

from otpstorm.providers.base import BaseProvider
from otpstorm.providers.registry import register_provider


@register_provider
class DmEducationProvider(BaseProvider):
    """Send OTP via dmeducation.lk API (Sri Lanka)."""

    name = "dmeducation"
    description = "DM Education OTP (Sri Lanka)"
    max_retries = 2
    request_timeout = 15

    def send(self, nomor: str, b: str, c: str) -> Dict[str, Any]:
        """
        Send OTP request to dmeducation.lk.

        The API expects the phone in local format with leading 0:
        {"mobile": "0701515609", "purpose": "register"}

        Args:
            nomor: Full phone number with leading 0 (e.g., 0701515609).
            b: Phone number without leading 0.
            c: Phone number with country code.

        Returns:
            Result dictionary.
        """
        url = "https://dmeducation.lk/api/auth/otp/request"

        # The API expects local format: 0701515609 (with leading 0)
        mobile = nomor  # e.g., 0701515609 or 094701515609

        # If the number has a country code prefix (e.g., 094...), strip it
        # to get the local format the API expects
        if mobile.startswith("094") and len(mobile) > 10:
            # User entered full number like 094701515609 → extract local 0701515609
            mobile = "0" + mobile[3:]  # Strip 094, add leading 0
        elif mobile.startswith("94") and len(mobile) > 9:
            # b starts with 94 but without leading 0
            # b = "94701515609" → mobile should be "0701515609"
            mobile = "0" + mobile[2:]  # Strip 94, add leading 0

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) "
                "Gecko/20100101 Firefox/128.0"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://dmeducation.lk/student/register",
            "Content-Type": "application/json",
            "Origin": "https://dmeducation.lk",
            "Alt-Used": "dmeducation.lk",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=0",
            "TE": "trailers",
        }

        payload = json.dumps({"mobile": mobile, "purpose": "register"})

        try:
            response = self._make_request(
                method="POST",
                url=url,
                headers=headers,
                data=payload,
            )

            message = f"HTTP {response.status_code}"
            try:
                resp_data = response.json()
                message = json.dumps(resp_data, ensure_ascii=False)[:150]
            except (json.JSONDecodeError, ValueError):
                if response.text:
                    message = self._truncate(response.text)

            success = response.status_code < 500

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
