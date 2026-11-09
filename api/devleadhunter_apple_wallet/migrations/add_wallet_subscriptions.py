"""
Migration: Apple Wallet — ``wallet_subscriptions`` table.

Recurring merchant billing for the Wallet module (Stripe subscriptions, free trial).
State mirrors the Stripe subscription and gates the merchant's access. Scoped to the
operator like the rest of the module.

Run with:
    python migrations/add_wallet_subscriptions.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from core.database import engine

_WALLET_SUBSCRIPTIONS_DDL = """
CREATE TABLE IF NOT EXISTS wallet_subscriptions (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  program_id INT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'incomplete',
  price_cents INT NOT NULL DEFAULT 0,
  currency VARCHAR(8) NOT NULL DEFAULT 'eur',
  stripe_customer_id VARCHAR(255) NULL,
  stripe_subscription_id VARCHAR(255) NULL,
  stripe_checkout_session_id VARCHAR(255) NULL,
  trial_ends_at DATETIME NULL,
  current_period_end DATETIME NULL,
  canceled_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NULL,
  KEY ix_wallet_subscriptions_user_id (user_id),
  KEY ix_wallet_subscriptions_program_id (program_id),
  KEY ix_wallet_subscriptions_status (status),
  KEY ix_wallet_subscriptions_stripe_customer_id (stripe_customer_id),
  KEY ix_wallet_subscriptions_stripe_subscription_id (stripe_subscription_id),
  KEY ix_wallet_subscriptions_stripe_checkout_session_id (stripe_checkout_session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def run_migration() -> None:
    print("Running migration: add_wallet_subscriptions")
    with engine.connect() as conn:
        conn.execute(text(_WALLET_SUBSCRIPTIONS_DDL))
        conn.commit()
    print("  + wallet_subscriptions table")
    print("Migration completed successfully.")


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Apple Wallet subscriptions table")
    print("=" * 60)
    run_migration()
