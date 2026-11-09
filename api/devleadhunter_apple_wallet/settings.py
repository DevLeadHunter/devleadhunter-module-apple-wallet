"""
The settings of the Apple Wallet module, read from the core's ``.env``.

The module owns its ``WALLET_*`` variables: they live in the same file as the core's (the ``.env`` the API runs with),
every other variable of which is ignored here.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppleWalletSettings(BaseSettings):
    """
    The ``WALLET_*`` settings: the Apple identifiers, the secret material seeded once, and the merchant's price.

    The certificates and keys only seed the encrypted credentials (``WalletCredentialsService.bootstrap_from_settings``):
    signing and pushing read the encrypted copy, never these values.

    Attributes:
        pass_type_identifier: Apple Pass Type ID (``WALLET_PASS_TYPE_IDENTIFIER``, e.g. ``pass.fr.dibodev.fidelite``).
        team_id: Apple Developer Team ID.
        apns_key_id: Key ID of the ``.p8`` APNs auth key.
        signing_certificate: Pass signing certificate (PEM).
        signing_private_key: Private signing key (PEM).
        wwdr_certificate: Apple WWDR intermediate certificate (PEM).
        apns_auth_key: ``.p8`` APNs auth key.
        subscription_price_cents: Monthly price of a merchant's card, in euro cents; ``{prix_carte}`` renders it.
        subscription_trial_days: Free-trial length of a merchant's subscription, in days.
    """

    model_config = SettingsConfigDict(
        env_prefix="WALLET_", env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    pass_type_identifier: str = Field(default="", description="Apple Pass Type ID")
    team_id: str = Field(default="", description="Apple Developer Team ID")
    apns_key_id: str = Field(default="", description="Key ID of the .p8 APNs auth key")
    signing_certificate: str = Field(default="", description="Pass signing certificate (PEM), seed only")
    signing_private_key: str = Field(default="", description="Private signing key (PEM), seed only")
    wwdr_certificate: str = Field(default="", description="Apple WWDR intermediate certificate (PEM), seed only")
    apns_auth_key: str = Field(default="", description=".p8 APNs auth key, seed only")
    subscription_price_cents: int = Field(default=1900, description="Monthly price of a merchant's card, in cents")
    subscription_trial_days: int = Field(default=30, description="Free-trial length of a subscription, in days")


wallet_settings = AppleWalletSettings()
