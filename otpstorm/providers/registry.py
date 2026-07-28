"""
Provider registry for OTPStorm.

Manages the collection of all available OTP providers and provides
filtering and selection mechanisms.
"""

from typing import Dict, List, Optional, Type

from otpstorm.providers.base import BaseProvider
from otpstorm.logger import get_logger

logger = get_logger("otpstorm.providers.registry")


class ProviderRegistry:
    """
    Registry of all available OTP providers.

    Providers register themselves via the @register_provider decorator
    or by calling registry.register().
    """

    _providers: Dict[str, Type[BaseProvider]] = {}
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, provider_cls: Type[BaseProvider]) -> Type[BaseProvider]:
        """
        Register a provider class.

        Can be used as a decorator:
            @ProviderRegistry.register
            class MyProvider(BaseProvider): ...

        Args:
            provider_cls: The provider class to register.

        Returns:
            The provider class (for decorator use).
        """
        name = provider_cls.name
        if name in cls._providers:
            logger.warning("Provider '%s' is already registered, overwriting.", name)
        cls._providers[name] = provider_cls
        logger.debug("Registered provider: %s", name)
        return provider_cls

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseProvider]]:
        """Get a provider class by name."""
        return cls._providers.get(name)

    @classmethod
    def get_all(cls) -> Dict[str, Type[BaseProvider]]:
        """Get all registered provider classes."""
        return dict(cls._providers)

    @classmethod
    def get_names(cls) -> List[str]:
        """Get a list of all registered provider names."""
        return list(cls._providers.keys())

    @classmethod
    def get_enabled(
        cls,
        enabled_list: Optional[str] = None,
        disabled_list: Optional[str] = None,
    ) -> Dict[str, Type[BaseProvider]]:
        """
        Get providers filtered by enabled/disabled lists.

        Args:
            enabled_list: Comma-separated provider names, or "all".
            disabled_list: Comma-separated provider names to exclude.

        Returns:
            Filtered dictionary of provider classes.
        """
        providers = cls._providers

        if enabled_list and enabled_list.lower() != "all":
            enabled_set = {name.strip() for name in enabled_list.split(",")}
            providers = {k: v for k, v in providers.items() if k in enabled_set}

        if disabled_list:
            disabled_set = {name.strip() for name in disabled_list.split(",")}
            providers = {k: v for k, v in providers.items() if k not in disabled_set}

        return providers

    @classmethod
    def count(cls) -> int:
        """Get the total number of registered providers."""
        return len(cls._providers)


# Convenience decorator
register_provider = ProviderRegistry.register
