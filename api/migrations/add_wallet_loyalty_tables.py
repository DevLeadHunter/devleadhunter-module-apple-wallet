"""
Migration: Apple Wallet loyalty module — data model tables.

Creates the five tables of the loyalty-card module (module 2): the merchant program,
the per-customer cards, the PassKit device registrations, the merchant automations,
and the append-only scan log. All rows are scoped to the owning operator (``user_id``),
matching the rest of the product. Tables are independent of the existing schema
(new feature), so the migration only creates them, idempotently.

Run with:
    python migrations/add_wallet_loyalty_tables.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from core.database import engine

_LOYALTY_PROGRAMS_DDL = """
CREATE TABLE IF NOT EXISTS loyalty_programs (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  prospect_id INT NULL,
  order_id INT NULL,
  organization_name VARCHAR(255) NOT NULL,
  description VARCHAR(255) NULL,
  stamps_required INT NOT NULL DEFAULT 10,
  reward_label VARCHAR(255) NULL,
  default_change_message TEXT NULL,
  logo_url TEXT NULL,
  background_color VARCHAR(32) NULL,
  foreground_color VARCHAR(32) NULL,
  label_color VARCHAR(32) NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NULL,
  deleted_at DATETIME NULL,
  KEY ix_loyalty_programs_user_id (user_id),
  KEY ix_loyalty_programs_prospect_id (prospect_id),
  KEY ix_loyalty_programs_order_id (order_id),
  KEY ix_loyalty_programs_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

_LOYALTY_CARDS_DDL = """
CREATE TABLE IF NOT EXISTS loyalty_cards (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  program_id INT NOT NULL,
  user_id INT NOT NULL,
  serial_number VARCHAR(64) NOT NULL,
  authentication_token VARCHAR(64) NOT NULL,
  stamps INT NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  holder_name VARCHAR(255) NULL,
  holder_email VARCHAR(255) NULL,
  marketing_consent_at DATETIME NULL,
  last_stamped_at DATETIME NULL,
  added_to_wallet_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NULL,
  UNIQUE KEY uq_loyalty_cards_serial_number (serial_number),
  KEY ix_loyalty_cards_program_id (program_id),
  KEY ix_loyalty_cards_user_id (user_id),
  KEY ix_loyalty_cards_status (status),
  CONSTRAINT fk_loyalty_cards_program
    FOREIGN KEY (program_id) REFERENCES loyalty_programs (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

_WALLET_DEVICE_REGISTRATIONS_DDL = """
CREATE TABLE IF NOT EXISTS wallet_device_registrations (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  card_id INT NOT NULL,
  user_id INT NOT NULL,
  device_library_identifier VARCHAR(255) NOT NULL,
  push_token VARCHAR(255) NOT NULL,
  pass_type_identifier VARCHAR(255) NOT NULL,
  serial_number VARCHAR(64) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NULL,
  UNIQUE KEY uq_wallet_registration_device_serial (device_library_identifier, serial_number),
  KEY ix_wallet_device_registrations_card_id (card_id),
  KEY ix_wallet_device_registrations_user_id (user_id),
  KEY ix_wallet_device_registrations_device (device_library_identifier),
  KEY ix_wallet_device_registrations_serial (serial_number),
  CONSTRAINT fk_wallet_registration_card
    FOREIGN KEY (card_id) REFERENCES loyalty_cards (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

_LOYALTY_AUTOMATIONS_DDL = """
CREATE TABLE IF NOT EXISTS loyalty_automations (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  program_id INT NOT NULL,
  user_id INT NOT NULL,
  name VARCHAR(255) NULL,
  trigger_type VARCHAR(20) NOT NULL,
  delay_minutes INT NOT NULL DEFAULT 0,
  field_key VARCHAR(64) NULL,
  field_value VARCHAR(255) NULL,
  change_message TEXT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NULL,
  KEY ix_loyalty_automations_program_id (program_id),
  KEY ix_loyalty_automations_user_id (user_id),
  KEY ix_loyalty_automations_trigger_type (trigger_type),
  CONSTRAINT fk_loyalty_automations_program
    FOREIGN KEY (program_id) REFERENCES loyalty_programs (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

_LOYALTY_SCAN_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS loyalty_scan_events (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  card_id INT NOT NULL,
  program_id INT NOT NULL,
  user_id INT NOT NULL,
  stamps_delta INT NOT NULL DEFAULT 1,
  stamps_after INT NOT NULL,
  source VARCHAR(20) NOT NULL DEFAULT 'merchant_scan',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_loyalty_scan_events_card_id (card_id),
  KEY ix_loyalty_scan_events_program_id (program_id),
  KEY ix_loyalty_scan_events_user_id (user_id),
  CONSTRAINT fk_loyalty_scan_events_card
    FOREIGN KEY (card_id) REFERENCES loyalty_cards (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

# Foreign keys constrain the order: programs, then cards, then everything referencing cards.
_TABLES: list[tuple[str, str]] = [
    ("loyalty_programs", _LOYALTY_PROGRAMS_DDL),
    ("loyalty_cards", _LOYALTY_CARDS_DDL),
    ("wallet_device_registrations", _WALLET_DEVICE_REGISTRATIONS_DDL),
    ("loyalty_automations", _LOYALTY_AUTOMATIONS_DDL),
    ("loyalty_scan_events", _LOYALTY_SCAN_EVENTS_DDL),
]


def run_migration() -> None:
    print("Running migration: add_wallet_loyalty_tables")
    with engine.connect() as conn:
        for table_name, ddl in _TABLES:
            conn.execute(text(ddl))
            print(f"  + {table_name} table")
        conn.commit()
    print("Migration completed successfully.")


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Apple Wallet loyalty module tables")
    print("=" * 60)
    run_migration()
