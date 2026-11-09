"""Add ``loyalty_cards.current_offer``, the offer of the moment an automation writes on a card.

The pass shows it as a field whose change triggers the lock-screen notification. A table created from the models
already has the column: nothing to do then.

Run alone from the core's ``api/``: ``python -m devleadhunter_apple_wallet.migrations.add_loyalty_card_current_offer``.
"""

from __future__ import annotations

from sqlalchemy.engine import Engine

from core.database import engine as core_engine

from devleadhunter_apple_wallet.migrations.schema_changes import WalletSchemaChanges


def run_migration(engine: Engine | None = None) -> None:
    """
    Add the column to a cards table that lacks it.

    Args:
        engine: The database to migrate, the core's when omitted.
    """
    added: bool = WalletSchemaChanges(engine or core_engine).add_missing_column(
        "loyalty_cards", "current_offer", "VARCHAR(255)"
    )
    print(f"add_loyalty_card_current_offer: column {'added' if added else 'present'}")


if __name__ == "__main__":
    run_migration()
