"""Create ``merchant_accounts``, the merchants' logins to their own space.

One account per loyalty program, apart from the operator's ``users`` (the handover model of the Storyblok space for
the websites). Re-runnable.

Run alone from the core's ``api/``: ``python -m devleadhunter_apple_wallet.migrations.add_merchant_accounts``.
"""

from __future__ import annotations

from sqlalchemy.engine import Engine

from core.database import engine as core_engine

from devleadhunter_apple_wallet.migrations.schema_changes import WalletSchemaChanges
from devleadhunter_apple_wallet.models.merchant_account import MerchantAccount


def run_migration(engine: Engine | None = None) -> None:
    """
    Create the merchant accounts table when it is missing.

    Args:
        engine: The database to migrate, the core's when omitted.
    """
    created: list[str] = WalletSchemaChanges(engine or core_engine).create_missing_tables(MerchantAccount)
    print(f"add_merchant_accounts: created {', '.join(created) or 'nothing (present)'}")


if __name__ == "__main__":
    run_migration()
