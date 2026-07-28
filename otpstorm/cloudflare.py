"""
Cloudflare bypass utilities for OTPStorm.

Uses `cloudscraper` to automatically solve Cloudflare JavaScript challenges
and extract clearance cookies, eliminating the need for manual cookie injection.

Also handles CSRF token extraction for sites that require it.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger("otpstorm.cloudflare")

# Optional dependency — cloudscraper might not always be available
_cloudscraper_available = False
try:
    import cloudscraper as _cs
    _cloudscraper_available = True
except ImportError:
    _cloudscraper_available = False


def is_available() -> bool:
    """Check if cloudscraper is installed."""
    return _cloudscraper_available


def create_cloudflare_session() -> Optional[object]:
    """
    Create a cloudscraper session that can bypass Cloudflare challenges.

    The session automatically:
    - Emulates browser TLS fingerprints
    - Solves JavaScript challenge pages
    - Retains clearance cookies across requests

    Returns:
        A cloudscraper.CloudScraper instance, or None if creation fails.
    """
    if not _cloudscraper_available:
        logger.warning("cloudscraper not installed. Install with: pip install cloudscraper")
        return None

    try:
        # Use minimal args — different cloudscraper versions have different signatures
        scraper = _cs.create_scraper(
            browser={"browser": "chrome", "mobile": False, "platform": "linux"},
        )
        logger.debug("Cloudflare bypass session created")
        return scraper
    except TypeError:
        # Fallback for older cloudscraper versions without browser dict support
        try:
            scraper = _cs.create_scraper()
            logger.debug("Cloudflare bypass session created (legacy)")
            return scraper
        except Exception as e:
            logger.error("Failed to create cloudscraper session: %s", e)
            return None
    except Exception as e:
        logger.error("Failed to create cloudscraper session: %s", e)
        return None


def extract_csrf_token(
    html: str,
    patterns: Optional[list] = None,
) -> Optional[str]:
    """
    Extract a CSRF token from HTML response.

    Tries multiple common patterns:
    - <meta name="csrf-token" content="...">
    - <input name="_token" value="...">
    - <input name="csrf_token" value="...">
    - <input name="csrfmiddlewaretoken" value="...">
    - Script variable csrfToken = "..."

    Args:
        html: HTML string to search.
        patterns: Optional list of custom regex patterns.

    Returns:
        Extracted token string, or None if not found.
    """
    if not html:
        return None

    default_patterns = patterns or [
        # Meta tag (most common)
        r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']',
        r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']csrf-token["\']',
        # Input fields
        r'<input[^>]*name=["\']_token["\'][^>]*value=["\']([^"\']+)["\']',
        r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']',
        r'<input[^>]*name=["\']csrfmiddlewaretoken["\'][^>]*value=["\']([^"\']+)["\']',
        # Script variable
        r'csrfToken\s*[=:]\s*["\']([^"\']+)["\']',
        r'csrf_token\s*[=:]\s*["\']([^"\']+)["\']',
    ]

    for pattern in default_patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            token = match.group(1)
            if token and len(token) > 5:
                return token

    return None
