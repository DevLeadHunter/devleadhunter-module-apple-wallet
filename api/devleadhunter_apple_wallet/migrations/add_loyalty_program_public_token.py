"""
Migration: Apple Wallet — ``loyalty_programs.public_token``.

The public enrollment flow (``POST /wallet/add/{public_token}``) resolves a merchant
program by an unguessable token instead of its internal id. The unique index is created
by the ORM on fresh databases; this migration adds the column to any pre-existing table.

Run with:
    python migrations/add_loyalty_program_public_token.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from core.database import engine


def run_migration() -> None:
    print("Running migration: add_loyalty_program_public_token")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE loyalty_programs ADD COLUMN IF NOT EXISTS public_token VARCHAR(64) NULL"))
        conn.commit()
    print("  + loyalty_programs.public_token")
    print("Migration completed successfully.")


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: loyalty_programs.public_token")
    print("=" * 60)
    run_migration()
