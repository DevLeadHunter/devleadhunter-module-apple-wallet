"""
Migration: ``merchant_accounts`` table — a merchant's login to their wallet dashboard.

One account per loyalty program, separate from the operator's ``users`` — the dedicated
client surface (like the Storyblok handover for websites).

Run with:
    python migrations/add_merchant_accounts.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from core.database import engine

_MERCHANT_ACCOUNTS_DDL = """
CREATE TABLE IF NOT EXISTS merchant_accounts (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  program_id INT NOT NULL,
  email VARCHAR(255) NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  last_login_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NULL,
  UNIQUE KEY uq_merchant_accounts_program_id (program_id),
  UNIQUE KEY uq_merchant_accounts_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def run_migration() -> None:
    print("Running migration: add_merchant_accounts")
    with engine.connect() as conn:
        conn.execute(text(_MERCHANT_ACCOUNTS_DDL))
        conn.commit()
    print("  + merchant_accounts table")
    print("Migration completed successfully.")


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: merchant_accounts table")
    print("=" * 60)
    run_migration()
