"""
Utility functions for OTPStorm.

Includes phone formatting, color output, typing animation, and status tracking.
"""

import sys
import time
import re
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


# ─── Terminal Color Constants ───────────────────────────────────────────────

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = "\033[1;92m"
    WHITE = "\033[1;97m"
    GRAY = "\033[1;90m"
    YELLOW = "\033[1;93m"
    PURPLE = "\033[1;95m"
    RED = "\033[1;91m"
    CYAN = "\033[1;96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"
    CLEAR_LINE = "\033[K"

    @classmethod
    def colorize(cls, text: str, color: str, bold: bool = False) -> str:
        """Wrap text in ANSI color codes."""
        prefix = cls.BOLD if bold else ""
        return f"{prefix}{color}{text}{cls.RESET}"


# ─── Status / Result Tracking ──────────────────────────────────────────────

@dataclass
class ProviderResult:
    """Result of a single provider OTP attempt."""
    provider_name: str
    success: bool
    status_code: Optional[int] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        icon = "✓" if self.success else "✗"
        color = Colors.GREEN if self.success else Colors.RED
        status = f"HTTP {self.status_code}" if self.status_code else "N/A"
        return (
            f"{color}{icon}{Colors.RESET} "
            f"{Colors.WHITE}{self.provider_name:<25}{Colors.RESET} "
            f"{Colors.GRAY}[{status}]{Colors.RESET} "
            f"{color}{self.message[:50]}{Colors.RESET} "
            f"{Colors.DIM}({self.duration_ms:.0f}ms){Colors.RESET}"
        )


@dataclass
class AttackSummary:
    """Summary of a full attack cycle."""
    total_providers: int = 0
    successes: int = 0
    failures: int = 0
    total_duration_ms: float = 0.0
    results: list = field(default_factory=list)

    def add_result(self, result: ProviderResult) -> None:
        """Add a provider result and update counts."""
        self.results.append(result)
        self.total_providers += 1
        if result.success:
            self.successes += 1
        else:
            self.failures += 1

    def print_summary(self, loop_number: int = 1) -> None:
        """Print a colored summary of the attack cycle."""
        print()
        print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
        print(
            f"{Colors.BOLD}{Colors.YELLOW}  Loop #{loop_number} Complete  "
            f"|  {Colors.GREEN}✓ {self.successes}{Colors.RESET}  "
            f"{Colors.RED}✗ {self.failures}{Colors.RESET}  "
            f"{Colors.WHITE}Total: {self.total_providers}{Colors.RESET}  "
            f"{Colors.DIM}({self.total_duration_ms:.0f}ms){Colors.RESET}"
        )
        print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
        print()


# ─── Phone Number Formatting ────────────────────────────────────────────────

def parse_phone_number(phone: str, country_code: str = "62") -> tuple:
    """
    Parse and normalize a phone number.

    Returns a tuple of (nomor, b, c) where:
        - nomor: Full number as entered by user (e.g., 089508226367)
        - b: Last 10-11 digits without leading 0 (e.g., 89508226367)
        - c: Number with country code prefix (e.g., 6289508226367)

    Args:
        phone: Raw phone number input.
        country_code: Country code (default 62 for Indonesia).

    Returns:
        Tuple of (nomor, b, c) formatted strings.

    Raises:
        ValueError: If the phone number is invalid.
    """
    # Strip all non-digit characters
    digits = re.sub(r"\D", "", phone)

    if not digits:
        raise ValueError("Phone number is empty")

    # Normalize
    if digits.startswith(f"+{country_code}"):
        nomor = "0" + digits[len(country_code) + 1:]
    elif digits.startswith(country_code):
        nomor = "0" + digits[len(country_code):]
    elif digits.startswith("0"):
        nomor = digits
    else:
        nomor = "0" + digits

    # Extract parts
    b = nomor[1:]  # Without leading 0
    c = country_code + b  # With country code

    # Validate length (minimum 10 digits including leading 0)
    if len(digits) < 10:
        raise ValueError(f"Phone number too short: {len(digits)} digits (minimum 10)")

    return nomor, b, c


def validate_phone(phone: str) -> bool:
    """Quick validation whether a string looks like a phone number."""
    try:
        parse_phone_number(phone)
        return True
    except ValueError:
        return False


# ─── Display Utilities ─────────────────────────────────────────────────────

_TYPING_ENABLED = True
_TYPING_SPEED = 0.03


def set_typing(enabled: bool, speed: float = 0.03) -> None:
    """Configure typing animation settings."""
    global _TYPING_ENABLED, _TYPING_SPEED
    _TYPING_ENABLED = enabled
    _TYPING_SPEED = speed


def typewrite(text: str, end: str = "\n") -> None:
    """
    Print text with a typing animation effect.

    Args:
        text: The text to print.
        end: String appended after the last character (default newline).
    """
    if _TYPING_ENABLED:
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(_TYPING_SPEED)
        sys.stdout.write(end)
        sys.stdout.flush()
    else:
        print(text, end=end)


def print_banner() -> None:
    """Print the OTPStorm ASCII banner."""
    banner = f"""{Colors.RED}
   ___ _____ ____   _____ _                  
  / _ \\_   _|  _ \\ / ___| |___  ___ __ _ ___ 
 | | | || | | |_) | |   | / __|/ __/ _` / __|
 | |_| || | |  __/| |___| \\__ \\ (_| (_| \\__ \\
  \\___/ |_| |_|    \\____|_|___/\\___\\__,_|___/
{Colors.RESET}
{Colors.YELLOW}  ⚡ Multi-Provider OTP Flood Tool v2.0.0{Colors.RESET}
{Colors.GRAY}  ⚠  For educational purposes only{Colors.RESET}
{Colors.CYAN}{'─' * 60}{Colors.RESET}
"""
    print(banner)


def print_countdown(
    seconds: int,
    label: str = "Next cycle",
    show_time: bool = True,
) -> None:
    """
    Display a countdown timer on a single line.

    Args:
        seconds: Number of seconds to count down.
        label: Text label for the countdown.
        show_time: Whether to show the current time alongside.
    """
    for remaining in range(seconds, 0, -1):
        mins, secs = divmod(remaining, 60)
        time_str = f"{label} in {Colors.GREEN}{mins:02d}:{secs:02d}{Colors.RESET}"

        if show_time:
            now = datetime.now()
            weekday = now.strftime("%A")
            date_str = now.strftime("%H:%M:%S")
            time_str += (
                f"  |  {Colors.CYAN}{weekday}, "
                f"{now.day} {now.strftime('%B')} {now.year}{Colors.RESET}  "
                f"|  {Colors.YELLOW}Time {date_str}{Colors.RESET}"
            )

        sys.stdout.write(f"\r{time_str}{Colors.CLEAR_LINE}")
        sys.stdout.flush()
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print()
            return
    print()


# ─── Miscellaneous ─────────────────────────────────────────────────────────

def clear_screen() -> None:
    """Clear the terminal screen."""
    import os
    os.system("cls" if os.name == "nt" else "clear")
