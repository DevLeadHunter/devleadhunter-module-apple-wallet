"""Wallet enrollment service — the public 'add the card to Wallet' entry point.

A customer opens the merchant's enrollment link (a QR at the counter): we mint a fresh
loyalty card for that program and hand back the signed ``.pkpass``. Enrollment is
idempotent per known customer — a repeat scan with the same email reuses their card
rather than minting a tenth one; anonymous adds cannot be de-duplicated server-side.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from enums.loyalty_card_status import LoyaltyCardStatus
from models.loyalty_card import LoyaltyCard
from models.loyalty_program import LoyaltyProgram
from services.wallet_pass_service import wallet_pass_service

_SERIAL_BYTES = 16
_TOKEN_BYTES = 24
_PUBLIC_TOKEN_BYTES = 12


class WalletEnrollmentError(RuntimeError):
    """Raised when a card cannot be enrolled (e.g. an unknown program token)."""


class WalletEnrollmentService:
    """Resolves a program by its public token and issues a card + its ``.pkpass``."""

    def ensure_public_token(self, db: Session, program: LoyaltyProgram) -> str:
        """Return the program's public token, generating and persisting one if absent.

        Args:
            db: Database session.
            program: The program to expose publicly.

        Returns:
            The public token.
        """
        if program.public_token:
            return program.public_token
        program.public_token = secrets.token_urlsafe(_PUBLIC_TOKEN_BYTES)
        db.commit()
        return program.public_token

    def get_public_program(self, db: Session, public_token: str) -> LoyaltyProgram | None:
        """Return the live program a public enrollment token points to, or ``None``.

        Args:
            db: Database session.
            public_token: The token from the enrollment URL.

        Returns:
            The program, or ``None`` when the token matches nothing (unknown or deleted).
        """
        return (
            db.query(LoyaltyProgram)
            .filter(LoyaltyProgram.public_token == public_token, LoyaltyProgram.deleted_at.is_(None))
            .first()
        )

    def add_card(
        self,
        db: Session,
        *,
        public_token: str,
        holder_name: str | None = None,
        holder_email: str | None = None,
        consent: bool = False,
    ) -> tuple[LoyaltyCard, bytes]:
        """Enroll a customer: reuse or mint their card, then build its signed ``.pkpass``.

        Args:
            db: Database session.
            public_token: The program's public handle from the enrollment URL.
            holder_name: Customer name, when collected.
            holder_email: Customer email — the idempotency key when present.
            consent: Whether the customer opted into marketing pushes (RGPD).

        Returns:
            The enrolled card and its ``.pkpass`` bytes.

        Raises:
            WalletEnrollmentError: When no active program matches the token.
        """
        program = self.get_public_program(db, public_token)
        if program is None:
            raise WalletEnrollmentError(f"No loyalty program for public token {public_token!r}.")
        card = self._existing_card(db, program, holder_email) or self._mint_card(
            db, program, holder_name=holder_name, holder_email=holder_email, consent=consent
        )
        pkpass = wallet_pass_service.generate_for_card(db, program.user_id, card.id)
        return card, pkpass

    @staticmethod
    def _existing_card(db: Session, program: LoyaltyProgram, holder_email: str | None) -> LoyaltyCard | None:
        """Return the customer's live card for this program, matched by email."""
        if not holder_email:
            return None
        return (
            db.query(LoyaltyCard)
            .filter(
                LoyaltyCard.program_id == program.id,
                LoyaltyCard.holder_email == holder_email,
                LoyaltyCard.status != LoyaltyCardStatus.REVOKED.value,
            )
            .first()
        )

    def _mint_card(
        self,
        db: Session,
        program: LoyaltyProgram,
        *,
        holder_name: str | None,
        holder_email: str | None,
        consent: bool,
    ) -> LoyaltyCard:
        """Create and persist a fresh card for a program."""
        card = LoyaltyCard(
            program_id=program.id,
            user_id=program.user_id,
            serial_number=secrets.token_urlsafe(_SERIAL_BYTES),
            authentication_token=secrets.token_urlsafe(_TOKEN_BYTES),
            holder_name=holder_name,
            holder_email=holder_email,
            marketing_consent_at=datetime.now(UTC).replace(tzinfo=None) if consent else None,
        )
        db.add(card)
        db.commit()
        db.refresh(card)
        return card


wallet_enrollment_service = WalletEnrollmentService()
