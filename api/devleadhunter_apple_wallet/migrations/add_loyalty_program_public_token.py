"""Add ``loyalty_programs.public_token``, the unguessable handle of a program's public enrollment link.

The public enrollment (``POST /wallet/add/{public_token}``) resolves a merchant's program by this token rather than
by its id. A table created from the models already has the column and its unique index: nothing to do then.

Run alone from the core's ``api/``: ``python -m devleadhunter_apple_wallet.migrations.add_loyalty_program_public_token``.
"""

from __future__ import annotations

from sqlalchemy.engine import Engine

from core.database import engine as core_engine

from devleadhunter_apple_wallet.migrations.schema_changes import WalletSchemaChanges


def run_migration(engine: Engine | None = None) -> None:
    """
    Add the column and its unique index to a programs table that lacks them.

    Args:
        engine: The database to migrate, the core's when omitted.
    """
    changes = WalletSchemaChanges(engine or core_engine)
    added_column: bool = changes.add_missing_column("loyalty_programs", "public_token", "VARCHAR(64)")
    added_index: bool = changes.add_missing_unique_index(
        "loyalty_programs", "ix_loyalty_programs_public_token", "public_token"
    )
    print(
        f"add_loyalty_program_public_token: column {'added' if added_column else 'present'}, "
        f"index {'added' if added_index else 'present'}"
    )


if __name__ == "__main__":
    run_migration()
