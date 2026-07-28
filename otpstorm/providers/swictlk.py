"""
Provider for swict.lk OTP API (Sri Lanka).

Endpoint: POST https://swict.lk/api/auth/send-otp
Source: User-provided curl command
"""

import json
import os
from typing import Dict, Any

from otpstorm.providers.base import BaseProvider
from otpstorm.providers.registry import register_provider
from otpstorm.cloudflare import extract_csrf_token as _extract_csrf


@register_provider
class SwictLkProvider(BaseProvider):
    """Send OTP via swict.lk API (Sri Lanka)."""

    name = "swictlk"
    description = "SWICT Lanka OTP (Sri Lanka)"
    max_retries = 2
    request_timeout = 30
    use_cloudscraper = True
    csrf_extract_url = "https://swict.lk/signup"

    def send(self, nomor: str, b: str, c: str) -> Dict[str, Any]:
        """
        Send OTP request to swict.lk.

        Uses exact headers from the provided curl command.
        Phone is sent as JSON in format {"phone": "94XXXXXXXXX"}.

        The `parse_phone_number()` utility assumes Indonesian (+62) by default,
        so `c` will have the wrong country code for Sri Lanka. We detect the
        correct +94 format from `b` directly.

        Args:
            nomor: Full phone number with leading 0 (e.g., 0701515602).
            b: Phone number without leading 0 (may already include 94 prefix).
            c: Phone number with country code (NOT used — uses +94 detection).

        Returns:
            Result dictionary.
        """
        url = "https://swict.lk/api/auth/send-otp"

        # Detect if b already contains the +94 country code
        # e.g., b="94701515609" → already has 94 → use as-is
        # e.g., b="701515602" → no country code → prepend 94
        if b.startswith("94"):
            phone_with_code = b
        else:
            phone_with_code = "94" + b

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) "
                "Gecko/20100101 Firefox/128.0"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://swict.lk/signup",
            "Content-Type": "application/json",
            "Origin": "https://swict.lk",
            "Alt-Used": "swict.lk",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=0",
        }

        # Cloudflare cookie support: users can inject fresh cf_clearance/csrf_token
        # via config file or env var. Set in otpstorm_config.json:
        #   {"cookies": {"swictlk": "cf_clearance=...; csrf_token=..."}}
        # Or via env: OTPSTORM_COOKIE_SWICTLK=cf_clearance=...;csrf_token=...
        # Check config file + env var for Cloudflare cookies
        cookie = (
            self.config.get("cookies", {}).get("swictlk", "")
            or self.config.get("cookie_swictlk", "")
            or os.environ.get("OTPSTORM_COOKIE_SWICTLK", "")
        )
        if cookie:
            headers["Cookie"] = cookie

        # Auto-fetch CSRF token from signup page (cloudscraper bypasses Cloudflare)
        csrf_token = None
        if self.csrf_extract_url:
            try:
                csrf_resp = self.session.get(
                    self.csrf_extract_url,
                    headers=headers,
                    timeout=self.request_timeout,
                )
                csrf_token = _extract_csrf(csrf_resp.text)
                if csrf_token:
                    headers["X-CSRF-Token"] = csrf_token
                    self.logger.debug("Extracted CSRF token: %s...", csrf_token[:20])
            except Exception as exc:
                self.logger.debug("CSRF extraction skipped: %s", exc)

        payload = json.dumps({"phone": phone_with_code})

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
