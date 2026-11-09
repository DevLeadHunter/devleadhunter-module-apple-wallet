"""Write the loyalty-card cold emails (« Carte fidélité - … ») on the admin's email library.

Already applied in production under this very name, when the templates still lived in the core: the runner skips it
there. Wherever it has not run, it upserts the five templates of the module on the admin's LIBRARY rows
(``is_library = 1``): an existing row gets the canonical subject, body, variables, category and sort order (and the
admin's preferred signature when it has none); a missing one is inserted, plain. The templates the admin wrote himself
(``is_library = 0``) are never touched. Without the admin user — a fresh database, seeded after the migrations — it
does nothing, and the core's seeder appends the module's library instead. Re-runnable.

Run alone from the core's ``api/``: ``python -m devleadhunter_apple_wallet.migrations.add_loyalty_card_email_templates``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from sqlalchemy import Table, insert, select, update
from sqlalchemy.engine import Connection, Engine

from core.clock import naive_utc_now
from core.config import settings
from core.database import engine as core_engine
from enums.email_template_layout import EmailTemplateLayout
from models.email_signature import EmailSignature
from models.email_template import EmailTemplate
from models.user import User

from devleadhunter_apple_wallet.campaigns.email_templates import LOYALTY_CARD_EMAIL_TEMPLATES

_VARIABLE_PATTERN: re.Pattern[str] = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


@dataclass(frozen=True)
class UpsertOutcome:
    """How many library rows the upsert rewrote and inserted."""

    rewritten: int
    inserted: int


class LoyaltyCardEmailTemplatesUpsert:
    """Writes the card's cold emails on the admin's library rows, matched by name."""

    def __init__(self, connection: Connection) -> None:
        self._connection: Connection = connection
        self._users: Table = User.__table__  # type: ignore[assignment]
        self._templates: Table = EmailTemplate.__table__  # type: ignore[assignment]
        self._signatures: Table = EmailSignature.__table__  # type: ignore[assignment]

    def run(self) -> UpsertOutcome | None:
        """
        Upsert every card template for the admin user.

        Returns:
            What was written, or None when the admin user does not exist yet.
        """
        admin_id: int | None = self._connection.execute(
            select(self._users.c.id).where(self._users.c.email == settings.admin_email)
        ).scalar()
        if admin_id is None:
            return None
        signature_id: int | None = self._connection.execute(
            select(self._signatures.c.id)
            .where(self._signatures.c.user_id == admin_id)
            .order_by(self._signatures.c.is_default.desc(), self._signatures.c.id)
            .limit(1)
        ).scalar()
        rewritten = 0
        inserted = 0
        for template in LOYALTY_CARD_EMAIL_TEMPLATES:
            values: dict[str, object] = self._canonical_values(template)
            existing_id: int | None = self._library_row_id(admin_id, str(template["name"]))
            if existing_id is None:
                self._connection.execute(
                    insert(self._templates).values(
                        user_id=admin_id,
                        name=str(template["name"]),
                        is_active=True,
                        is_library=True,
                        signature_id=signature_id,
                        layout=EmailTemplateLayout.PLAIN.value,
                        created_at=naive_utc_now(),
                        **values,
                    )
                )
                inserted += 1
                continue
            current_signature_id: int | None = self._connection.execute(
                select(self._templates.c.signature_id).where(self._templates.c.id == existing_id)
            ).scalar()
            self._connection.execute(
                update(self._templates)
                .where(self._templates.c.id == existing_id)
                .values(is_active=True, signature_id=current_signature_id or signature_id, **values)
            )
            rewritten += 1
        return UpsertOutcome(rewritten=rewritten, inserted=inserted)

    def _library_row_id(self, admin_id: int, name: str) -> int | None:
        return self._connection.execute(
            select(self._templates.c.id).where(
                self._templates.c.user_id == admin_id,
                self._templates.c.is_library.is_(True),
                self._templates.c.name == name,
            )
        ).scalar()

    @staticmethod
    def _canonical_values(template: dict[str, object]) -> dict[str, object]:
        subject = str(template["subject"])
        body_html = str(template["body_html"])
        variables: list[str] = sorted(set(_VARIABLE_PATTERN.findall(f"{subject} {body_html}")))
        sort_order: object = template["sort_order"]
        return {
            "subject": subject,
            "body_html": body_html,
            "variables": json.dumps(variables),
            "category": str(template["category"]),
            "sort_order": sort_order if isinstance(sort_order, int) else 0,
        }


def run_migration(engine: Engine | None = None) -> None:
    """
    Upsert the card's cold emails on the admin's library, in one transaction.

    Args:
        engine: The database to migrate, the core's when omitted.
    """
    with (engine or core_engine).begin() as connection:
        outcome: UpsertOutcome | None = LoyaltyCardEmailTemplatesUpsert(connection).run()
    if outcome is None:
        print(f"add_loyalty_card_email_templates: admin {settings.admin_email!r} not found, the seeder will seed")
        return
    print(f"add_loyalty_card_email_templates: {outcome.rewritten} rewritten, {outcome.inserted} inserted")


if __name__ == "__main__":
    run_migration()
