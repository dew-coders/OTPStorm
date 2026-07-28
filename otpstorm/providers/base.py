"""
Base provider class for OTPStorm.

All OTP providers inherit from BaseProvider and implement the `send()` method.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from otpstorm.exceptions import ProviderError, NetworkError, RateLimitError

logger = logging.getLogger("otpstorm.providers")


class BaseProvider(ABC):
    """
    Abstract base class for OTP sending providers.

    Each subclass must define:
        - name: A unique human-readable provider name
        - send(): The method that performs the OTP request

    For Cloudflare-protected endpoints, set `use_cloudscraper = True`
    in the subclass. The provider will then automatically bypass
    Cloudflare challenges using the cloudscraper library.
    """

    # Provider metadata — override in subclasses
    name: str = "base_provider"
    description: str = "Base OTP provider"
    max_retries: int = 1
    request_timeout: int = 15
    use_cloudscraper: bool = False
    csrf_extract_url: Optional[str] = None

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the provider.

        Args:
            session: Reusable requests Session for connection pooling.
            config: Provider-specific configuration overrides.
        """
        self.config = config or {}

        # Use cloudscraper for Cloudflare-protected endpoints
        if self.use_cloudscraper:
            self.session = self._create_cloudscraper_session()
        else:
            self.session = session or self._create_default_session()

        self.logger = logging.getLogger(f"otpstorm.providers.{self.name}")

    @staticmethod
    def _create_default_session() -> requests.Session:
        """Create a requests Session with retry strategy."""
        session = requests.Session()

        retry_strategy = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    @staticmethod
    def _create_cloudscraper_session():
        """
        Create a cloudscraper session that auto-bypasses Cloudflare challenges.

        Falls back to a regular requests.Session if cloudscraper is not installed.
        """
        try:
            from otpstorm.cloudflare import create_cloudflare_session
            cf_session = create_cloudflare_session()
            if cf_session is not None:
                return cf_session
        except Exception as exc:
            logger.warning("cloudscraper unavailable, falling back to requests: %s", exc)

        import requests as _requests
        logger.info("Falling back to standard requests.Session (Cloudflare bypass disabled)")
        session = _requests.Session()
        retry = Retry(total=1, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    @abstractmethod
    def send(self, nomor: str, b: str, c: str) -> Dict[str, Any]:
        """
        Execute the OTP request against this provider's endpoint.

        Args:
            nomor: Full phone number with leading 0 (e.g., 089508226367).
            b: Phone number without leading 0 (e.g., 89508226367).
            c: Phone number with country code (e.g., 6289508226367).

        Returns:
            Dict with keys:
                - success (bool): Whether the request was sent.
                - status_code (int | None): HTTP status code.
                - message (str): Human-readable result message.
                - response_text (str | None): Truncated response body.
        """
        raise NotImplementedError

    def execute(self, nomor: str, b: str, c: str) -> Dict[str, Any]:
        """
        Execute the OTP request with retry logic and timing.

        Args:
            nomor: Full phone number with leading 0.
            b: Phone number without leading 0.
            c: Phone number with country code.

        Returns:
            Dict with result information.
        """
        start_time = time.time()
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                result = self.send(nomor, b, c)
                elapsed = (time.time() - start_time) * 1000
                result["duration_ms"] = elapsed
                result["provider_name"] = self.name
                return result

            except RateLimitError as e:
                last_error = e
                self.logger.warning(
                    "Rate limited on attempt %d/%d for %s: %s",
                    attempt, self.max_retries, self.name, e,
                )
                if attempt < self.max_retries:
                    time.sleep(2.0 * attempt)

            except (requests.ConnectionError, requests.Timeout) as e:
                last_error = NetworkError(f"Network error: {e}")
                self.logger.debug(
                    "Network error attempt %d/%d for %s: %s",
                    attempt, self.max_retries, self.name, e,
                )
                if attempt < self.max_retries:
                    time.sleep(1.0)

            except ProviderError:
                # Don't retry on provider errors — they're expected (e.g. invalid phone)
                raise

            except Exception as e:
                last_error = e
                self.logger.exception(
                    "Unexpected error on attempt %d/%d for %s",
                    attempt, self.max_retries, self.name,
                )
                if attempt < self.max_retries:
                    time.sleep(0.5)

        # All retries exhausted
        elapsed = (time.time() - start_time) * 1000
        return {
            "success": False,
            "provider_name": self.name,
            "status_code": getattr(last_error, "status_code", None),
            "message": str(last_error) if last_error else "Unknown error",
            "duration_ms": elapsed,
            "response_text": None,
        }

    def _make_request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> requests.Response:
        """
        Make an HTTP request with standard headers.

        Args:
            method: HTTP method (GET, POST, PUT).
            url: Request URL.
            **kwargs: Additional arguments for requests.request().

        Returns:
            Response object.

        Raises:
            NetworkError: On connection issues.
            RateLimitError: On HTTP 429.
        """
        headers = kwargs.pop("headers", {})
        headers.setdefault(
            "User-Agent",
            self.config.get(
                "user_agent",
                "Mozilla/5.0 (Linux; Android 10; SM-A107F) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36",
            ),
        )

        timeout = kwargs.pop("timeout", self.request_timeout)

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=timeout,
                **kwargs,
            )

            if response.status_code == 429:
                raise RateLimitError(
                    self.name,
                    "Rate limited",
                    status_code=429,
                )

            return response

        except (requests.ConnectionError, requests.Timeout) as e:
            raise NetworkError(f"Request to {url} failed: {e}") from e

    def _truncate(self, text: Optional[str], max_len: int = 200) -> str:
        """Truncate response text for logging."""
        if not text:
            return ""
        if len(text) > max_len:
            return text[:max_len] + "..."
        return text
