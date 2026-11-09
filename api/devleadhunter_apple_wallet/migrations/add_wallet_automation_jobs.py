"""Create ``wallet_automation_jobs``, the deferred runs of the loyalty automations.

An ``on_scan`` automation fires after a delay, a ``broadcast`` one goes to every card of a program: the worker loop
applies each due job's field change and pushes the update. Re-runnable.

Run alone from the core's ``api/``: ``python -m devleadhunter_apple_wallet.migrations.add_wallet_automation_jobs``.
"""

from __future__ import annotations

from sqlalchemy.engine import Engine

from core.database import engine as core_engine

from devleadhunter_apple_wallet.migrations.schema_changes import WalletSchemaChanges
from devleadhunter_apple_wallet.models.wallet_automation_job import WalletAutomationJob


def run_migration(engine: Engine | None = None) -> None:
    """
    Create the automation jobs table when it is missing.

    Args:
        engine: The database to migrate, the core's when omitted.
    """
    created: list[str] = WalletSchemaChanges(engine or core_engine).create_missing_tables(WalletAutomationJob)
    print(f"add_wallet_automation_jobs: created {', '.join(created) or 'nothing (present)'}")


if __name__ == "__main__":
    run_migration()
