"""Create the table of the operators' Apple signing and APNs material.

One row per operator. The secret columns (signing key and certificate, WWDR chain, APNs auth key) hold
``encryption_service`` ciphertext, never plaintext; the identifiers stay in clear. Re-runnable.

Run alone from the core's ``api/``: ``python -m devleadhunter_apple_wallet.migrations.add_wallet_credentials_table``.
"""

from __future__ import annotations

from sqlalchemy.engine import Engine

# The credentials point at the core's users: their table must be on the metadata to render the foreign key.
import models.user  # noqa: F401
from core.database import engine as core_engine

from devleadhunter_apple_wallet.migrations.schema_changes import WalletSchemaChanges
from devleadhunter_apple_wallet.models.wallet_credentials import WalletCredentials


def run_migration(engine: Engine | None = None) -> None:
    """
    Create the credentials table when it is missing.

    Args:
        engine: The database to migrate, the core's when omitted.
    """
    created: list[str] = WalletSchemaChanges(engine or core_engine).create_missing_tables(WalletCredentials)
    print(f"add_wallet_credentials_table: created {', '.join(created) or 'nothing (present)'}")


if __name__ == "__main__":
    run_migration()
