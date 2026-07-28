"""
Configuration management for OTPStorm.

Handles default settings, environment variables, and user configuration.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from otpstorm.exceptions import ConfigurationError


# Default configuration
DEFAULT_CONFIG = {
    # Request settings
    "timeout": 15,                 # Default HTTP timeout in seconds
    "max_retries": 2,              # Max retries per provider on failure
    "retry_delay": 1.0,            # Delay between retries in seconds
    "user_agent": "Mozilla/5.0 (Linux; Android 10; SM-A107F) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36",

    # Loop / attack settings
    "default_loops": 5,            # Default number of attack cycles
    "inter_loop_delay": 60,        # Delay between loops in seconds
    "request_delay": 0.5,          # Small delay between each provider request

    # Provider settings
    "enabled_providers": "all",    # "all" or comma-separated list
    "disabled_providers": "",      # Comma-separated list to exclude
    "provider_timeout": 10,        # Per-provider timeout

    # Logging
    "log_level": "INFO",           # DEBUG, INFO, WARNING, ERROR
    "log_file": None,              # Path to log file (None = stdout only)
    "log_rotation": False,         # Enable log file rotation

    # Display
    "color_output": True,          # Use ANSI color codes
    "typing_animation": True,      # Slow typing effect for messages
    "typing_speed": 0.03,          # Seconds per character in typing animation

    # Country code
    "default_country_code": "62",  # Indonesia
}


def get_config_path() -> Path:
    """Get the path to the user config file."""
    # Check for config in common locations
    for loc in [
        Path.cwd() / "otpstorm_config.json",
        Path.home() / ".otpstorm" / "config.json",
        Path.home() / ".config" / "otpstorm" / "config.json",
    ]:
        if loc.exists():
            return loc
    return Path.cwd() / "otpstorm_config.json"


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file, merging with defaults.

    Args:
        path: Optional path to config file. If None, searches default locations.

    Returns:
        Merged configuration dictionary.
    """
    config = DEFAULT_CONFIG.copy()

    if path:
        config_path = Path(path)
    else:
        config_path = get_config_path()

    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                user_config = json.load(f)
            config.update(user_config)
        except (json.JSONDecodeError, OSError) as e:
            raise ConfigurationError(f"Failed to load config from {config_path}: {e}")

    # Override with environment variables
    env_overrides = {
        "OTPSTORM_TIMEOUT": ("timeout", int),
        "OTPSTORM_LOG_LEVEL": ("log_level", str),
        "OTPSTORM_LOOPS": ("default_loops", int),
        "OTPSTORM_PROVIDERS": ("enabled_providers", str),
    }
    for env_var, (config_key, cast_fn) in env_overrides.items():
        if env_var in os.environ:
            config[config_key] = cast_fn(os.environ[env_var])

    return config


def save_config(config: Dict[str, Any], path: Optional[str] = None) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration dictionary to save.
        path: Path to save to. If None, uses default location.
    """
    save_path = Path(path) if path else get_config_path()
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "w") as f:
        json.dump(config, f, indent=2)
