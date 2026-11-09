"""
The tables of the Apple Wallet module.

Importing this package registers every one of them on the core's metadata, which is what the module's ``load()``
does before ``init_db()`` creates the missing tables.
"""

from devleadhunter_apple_wallet.models.loyalty_automation import LoyaltyAutomation
from devleadhunter_apple_wallet.models.loyalty_card import LoyaltyCard
from devleadhunter_apple_wallet.models.loyalty_program import LoyaltyProgram
from devleadhunter_apple_wallet.models.loyalty_scan_event import LoyaltyScanEvent
from devleadhunter_apple_wallet.models.merchant_account import MerchantAccount
from devleadhunter_apple_wallet.models.wallet_automation_job import WalletAutomationJob
from devleadhunter_apple_wallet.models.wallet_credentials import WalletCredentials
from devleadhunter_apple_wallet.models.wallet_device_registration import WalletDeviceRegistration
from devleadhunter_apple_wallet.models.wallet_subscription import WalletSubscription

__all__ = [
    "LoyaltyAutomation",
    "LoyaltyCard",
    "LoyaltyProgram",
    "LoyaltyScanEvent",
    "MerchantAccount",
    "WalletAutomationJob",
    "WalletCredentials",
    "WalletDeviceRegistration",
    "WalletSubscription",
]
