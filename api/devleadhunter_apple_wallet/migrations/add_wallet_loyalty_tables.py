"""Create the five tables of the loyalty cards: programs, cards, device registrations, automations and scan log.

Every row is scoped to the operator who sells the program (``user_id``), like the rest of the product. A table that
exists already is left as it is, so the migration can run again.

Run alone from the core's ``api/``: ``python -m devleadhunter_apple_wallet.migrations.add_wallet_loyalty_tables``.
"""

from __future__ import annotations

from sqlalchemy.engine import Engine

from core.database import engine as core_engine

from devleadhunter_apple_wallet.migrations.schema_changes import WalletSchemaChanges
from devleadhunter_apple_wallet.models.loyalty_automation import LoyaltyAutomation
from devleadhunter_apple_wallet.models.loyalty_card import LoyaltyCard
from devleadhunter_apple_wallet.models.loyalty_program import LoyaltyProgram
from devleadhunter_apple_wallet.models.loyalty_scan_event import LoyaltyScanEvent
from devleadhunter_apple_wallet.models.wallet_device_registration import WalletDeviceRegistration


def run_migration(engine: Engine | None = None) -> None:
    """
    Create the loyalty tables that are missing, each referenced table before the tables pointing at it.

    Args:
        engine: The database to migrate, the core's when omitted.
    """
    created: list[str] = WalletSchemaChanges(engine or core_engine).create_missing_tables(
        LoyaltyProgram, LoyaltyCard, WalletDeviceRegistration, LoyaltyAutomation, LoyaltyScanEvent
    )
    print(f"add_wallet_loyalty_tables: created {', '.join(created) or 'nothing (all present)'}")


if __name__ == "__main__":
    run_migration()
