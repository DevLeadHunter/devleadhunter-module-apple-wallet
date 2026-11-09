"""The module's migrations: each runs on SQLite as on MySQL, any number of times, after ``init_db()`` or alone."""

from __future__ import annotations

import importlib
import json
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from core.config import settings
from core.database import Base
from models.email_signature import EmailSignature
from models.email_template import EmailTemplate
from models.user import User

from devleadhunter_apple_wallet.campaigns.email_templates import LOYALTY_CARD_EMAIL_TEMPLATES
from devleadhunter_apple_wallet.migrations import add_loyalty_card_email_templates
from devleadhunter_apple_wallet.migrations.add_loyalty_card_email_templates import LoyaltyCardEmailTemplatesUpsert
from devleadhunter_apple_wallet.models import (
    LoyaltyAutomation,
    LoyaltyCard,
    LoyaltyProgram,
    LoyaltyScanEvent,
    MerchantAccount,
    WalletAutomationJob,
    WalletCredentials,
    WalletDeviceRegistration,
    WalletSubscription,
)
from devleadhunter_apple_wallet.module import AppleWalletModule

_WALLET_TABLES: frozenset[str] = frozenset(
    model.__tablename__
    for model in (
        LoyaltyAutomation,
        LoyaltyCard,
        LoyaltyProgram,
        LoyaltyScanEvent,
        MerchantAccount,
        WalletAutomationJob,
        WalletCredentials,
        WalletDeviceRegistration,
        WalletSubscription,
    )
)
_CARD_TEMPLATE_NAMES: list[str] = [str(template["name"]) for template in LOYALTY_CARD_EMAIL_TEMPLATES]


@pytest.fixture
def core_only_engine() -> Iterator[Engine]:
    """A database holding the core's tables and none of the module's, as before the module was installed."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(
        engine, tables=[table for table in Base.metadata.sorted_tables if table.name not in _WALLET_TABLES]
    )
    yield engine
    engine.dispose()


def _schema_of(engine: Engine) -> dict[str, list[tuple[str, str, bool]]]:
    """Each wallet table's columns, as (name, type, nullable)."""
    inspector = inspect(engine)
    return {
        table: [(column["name"], str(column["type"]), column["nullable"]) for column in inspector.get_columns(table)]
        for table in sorted(_WALLET_TABLES)
    }


def _run_schema_migrations(engine: Engine) -> None:
    for name, module_path in AppleWalletModule().migrations():
        if name != "add_loyalty_card_email_templates":
            importlib.import_module(module_path).run_migration(engine)


class TestSchema:
    def test_the_migrations_create_every_wallet_table_then_find_nothing_to_do(self, core_only_engine: Engine) -> None:
        _run_schema_migrations(core_only_engine)
        tables_after_first_run = set(inspect(core_only_engine).get_table_names())
        _run_schema_migrations(core_only_engine)

        assert tables_after_first_run >= _WALLET_TABLES
        assert set(inspect(core_only_engine).get_table_names()) == tables_after_first_run

    def test_the_tables_init_db_created_are_left_as_they_are(self, engine: Engine) -> None:
        schema_before = _schema_of(engine)
        _run_schema_migrations(engine)

        assert _schema_of(engine) == schema_before

    def test_a_table_older_than_its_columns_gets_them(self) -> None:
        engine = create_engine("sqlite://")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE loyalty_programs (id INTEGER PRIMARY KEY, organization_name TEXT)"))
            connection.execute(text("CREATE TABLE loyalty_cards (id INTEGER PRIMARY KEY, serial_number TEXT)"))
            connection.execute(text("INSERT INTO loyalty_programs (organization_name) VALUES ('A'), ('B')"))

        for name in ("add_loyalty_program_public_token", "add_loyalty_card_current_offer"):
            module = importlib.import_module(f"devleadhunter_apple_wallet.migrations.{name}")
            module.run_migration(engine)
            module.run_migration(engine)

        inspector = inspect(engine)
        assert "public_token" in {column["name"] for column in inspector.get_columns("loyalty_programs")}
        assert "current_offer" in {column["name"] for column in inspector.get_columns("loyalty_cards")}
        token_index = next(
            index
            for index in inspector.get_indexes("loyalty_programs")
            if index["name"] == "ix_loyalty_programs_public_token"
        )
        assert token_index["unique"]
        engine.dispose()


class TestEmailTemplates:
    @staticmethod
    def _admin(db: Session) -> User:
        admin = User(name="Admin", email=settings.admin_email, hashed_password="x")
        db.add(admin)
        db.commit()
        return admin

    @staticmethod
    def _library_rows(db: Session, admin: User) -> list[EmailTemplate]:
        db.expire_all()
        return (
            db.query(EmailTemplate)
            .filter(EmailTemplate.user_id == admin.id, EmailTemplate.name.in_(_CARD_TEMPLATE_NAMES))
            .order_by(EmailTemplate.id)
            .all()
        )

    def test_without_the_admin_nothing_is_written(self, engine: Engine, db: Session) -> None:
        """A fresh database: the core's seeder, run after the migrations, appends the module's library itself."""
        with engine.begin() as connection:
            assert LoyaltyCardEmailTemplatesUpsert(connection).run() is None
        assert db.query(EmailTemplate).count() == 0

    def test_the_card_templates_are_inserted_once_then_rewritten(self, engine: Engine, db: Session) -> None:
        admin = self._admin(db)
        db.add(EmailSignature(user_id=admin.id, name="Admin", content_html="<p>Admin</p>", is_default=True))
        db.commit()

        add_loyalty_card_email_templates.run_migration(engine)
        first_run = self._library_rows(db, admin)
        add_loyalty_card_email_templates.run_migration(engine)
        second_run = self._library_rows(db, admin)

        assert [row.name for row in first_run] == _CARD_TEMPLATE_NAMES
        assert [row.id for row in second_run] == [row.id for row in first_run]
        signature_id = db.query(EmailSignature.id).scalar()
        for row, template in zip(second_run, LOYALTY_CARD_EMAIL_TEMPLATES, strict=True):
            assert (row.subject, row.body_html, row.category) == (
                template["subject"],
                template["body_html"],
                template["category"],
            )
            assert row.is_library and row.is_active and row.signature_id == signature_id
            assert "lien_carte" in json.loads(row.variables or "[]")

    def test_a_drifted_library_row_is_rewritten_and_the_admin_own_template_left_alone(
        self, engine: Engine, db: Session
    ) -> None:
        admin = self._admin(db)
        name = _CARD_TEMPLATE_NAMES[0]
        db.add_all(
            [
                EmailTemplate(
                    user_id=admin.id, name=name, subject="ancien sujet", body_html="<p>x</p>", is_library=True
                ),
                EmailTemplate(
                    user_id=admin.id, name=name, subject="mon sujet", body_html="<p>moi</p>", is_library=False
                ),
            ]
        )
        db.commit()

        add_loyalty_card_email_templates.run_migration(engine)

        rows = {row.is_library: row for row in self._library_rows(db, admin) if row.name == name}
        assert rows[True].subject == LOYALTY_CARD_EMAIL_TEMPLATES[0]["subject"]
        assert (rows[False].subject, rows[False].body_html) == ("mon sujet", "<p>moi</p>")
