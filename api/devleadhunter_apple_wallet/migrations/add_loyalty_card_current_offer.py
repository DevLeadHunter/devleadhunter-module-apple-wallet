"""
Migration: Apple Wallet — ``loyalty_cards.current_offer``.

The automation engine writes the 'offer of the moment' onto a card; the pass renders it
as a field whose change triggers the lock-screen notification. The ORM creates the column
on fresh databases; this migration adds it to any pre-existing table.

Run with:
    python migrations/add_loyalty_card_current_offer.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from core.database import engine


def run_migration() -> None:
    print("Running migration: add_loyalty_card_current_offer")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE loyalty_cards ADD COLUMN IF NOT EXISTS current_offer VARCHAR(255) NULL"))
        conn.commit()
    print("  + loyalty_cards.current_offer")
    print("Migration completed successfully.")


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: loyalty_cards.current_offer")
    print("=" * 60)
    run_migration()
