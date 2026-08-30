"""
Migration: Apple Wallet module — encrypted credentials table.

Stores one row per operator holding the Apple signing + APNs material. The secret
columns (signing key/cert, WWDR, APNs auth key) hold ``encryption_service`` ciphertext,
never plaintext; the identifiers stay in clear.

Run with:
    python migrations/add_wallet_credentials_table.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from core.database import engine

_WALLET_CREDENTIALS_DDL = """
CREATE TABLE IF NOT EXISTS wallet_credentials (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  pass_type_identifier VARCHAR(255) NULL,
  team_id VARCHAR(64) NULL,
  apns_key_id VARCHAR(64) NULL,
  signing_certificate TEXT NULL,
  signing_private_key TEXT NULL,
  wwdr_certificate TEXT NULL,
  apns_auth_key TEXT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NULL,
  UNIQUE KEY uq_wallet_credentials_user_id (user_id),
  CONSTRAINT fk_wallet_credentials_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def run_migration() -> None:
    print("Running migration: add_wallet_credentials_table")
    with engine.connect() as conn:
        conn.execute(text(_WALLET_CREDENTIALS_DDL))
        conn.commit()
    print("  + wallet_credentials table")
    print("Migration completed successfully.")


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Apple Wallet credentials table")
    print("=" * 60)
    run_migration()
