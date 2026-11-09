"""Create ``wallet_subscriptions``, the merchants' monthly Stripe subscriptions to their card.

Their state mirrors the Stripe subscription (free trial included) and gates the merchant's access. Re-runnable.

Run alone from the core's ``api/``: ``python -m devleadhunter_apple_wallet.migrations.add_wallet_subscriptions``.
"""

from __future__ import annotations

from sqlalchemy.engine import Engine

from core.database import engine as core_engine

from devleadhunter_apple_wallet.migrations.schema_changes import WalletSchemaChanges
from devleadhunter_apple_wallet.models.wallet_subscription import WalletSubscription


def run_migration(engine: Engine | None = None) -> None:
    """
    Create the subscriptions table when it is missing.

    Args:
        engine: The database to migrate, the core's when omitted.
    """
    created: list[str] = WalletSchemaChanges(engine or core_engine).create_missing_tables(WalletSubscription)
    print(f"add_wallet_subscriptions: created {', '.join(created) or 'nothing (present)'}")


if __name__ == "__main__":
    run_migration()
