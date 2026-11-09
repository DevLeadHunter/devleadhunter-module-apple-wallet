"""
Migration: Apple Wallet — ``wallet_automation_jobs`` table.

Deferred automation jobs (``on_scan`` fired after a delay, or ``broadcast`` to a
program's cards): a worker loop applies each due job's field change and pushes the
update. Scoped to the owning operator like the rest of the module.

Run with:
    python migrations/add_wallet_automation_jobs.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from core.database import engine

_WALLET_AUTOMATION_JOBS_DDL = """
CREATE TABLE IF NOT EXISTS wallet_automation_jobs (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  automation_id INT NOT NULL,
  card_id INT NOT NULL,
  user_id INT NOT NULL,
  scheduled_at DATETIME NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  error VARCHAR(500) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  sent_at DATETIME NULL,
  KEY ix_wallet_automation_jobs_automation_id (automation_id),
  KEY ix_wallet_automation_jobs_card_id (card_id),
  KEY ix_wallet_automation_jobs_user_id (user_id),
  KEY ix_wallet_automation_jobs_scheduled_at (scheduled_at),
  KEY ix_wallet_automation_jobs_status (status),
  CONSTRAINT fk_wallet_automation_jobs_automation
    FOREIGN KEY (automation_id) REFERENCES loyalty_automations (id) ON DELETE CASCADE,
  CONSTRAINT fk_wallet_automation_jobs_card
    FOREIGN KEY (card_id) REFERENCES loyalty_cards (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def run_migration() -> None:
    print("Running migration: add_wallet_automation_jobs")
    with engine.connect() as conn:
        conn.execute(text(_WALLET_AUTOMATION_JOBS_DDL))
        conn.commit()
    print("  + wallet_automation_jobs table")
    print("Migration completed successfully.")


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Apple Wallet automation jobs table")
    print("=" * 60)
    run_migration()
