"""Loyalty program service — the operator-side CRUD for a merchant's card configuration.

The operator (who sells the module) creates one program per merchant, tunes its stamps,
reward and brand colors, and hands the merchant a login. Everything is scoped to the
operator's ``user_id``; a public enrollment token is minted on creation so the merchant's
"add to Wallet" link is ready as soon as the program exists.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from enums.loyalty_program_status import LoyaltyProgramStatus
from models.loyalty_program import LoyaltyProgram
from services.wallet_enrollment_service import wallet_enrollment_service

# Fields an operator may edit through an update; everything else (ids, token, status flow) is managed.
_EDITABLE_FIELDS = (
    "organization_name",
    "description",
    "stamps_required",
    "reward_label",
    "default_change_message",
    "logo_url",
    "background_color",
    "foreground_color",
    "label_color",
)


class WalletProgramError(RuntimeError):
    """Raised when a program cannot be found for the operator, or a change is invalid."""


class WalletProgramService:
    """Operator-scoped create / read / update of loyalty programs."""

    def list_for_user(self, db: Session, user_id: int) -> list[LoyaltyProgram]:
        """Return the operator's programs, most recently created first.

        Args:
            db: Database session.
            user_id: Operator whose programs to list.

        Returns:
            The non-deleted programs owned by the operator.
        """
        return (
            db.query(LoyaltyProgram)
            .filter(LoyaltyProgram.user_id == user_id, LoyaltyProgram.deleted_at.is_(None))
            .order_by(LoyaltyProgram.created_at.desc(), LoyaltyProgram.id.desc())
            .all()
        )

    def get_for_user(self, db: Session, user_id: int, program_id: int) -> LoyaltyProgram | None:
        """Return one of the operator's programs, or ``None``.

        Args:
            db: Database session.
            user_id: Operator who must own the program.
            program_id: The program to fetch.

        Returns:
            The program, or ``None`` when it does not exist or is not owned.
        """
        return (
            db.query(LoyaltyProgram)
            .filter(
                LoyaltyProgram.id == program_id,
                LoyaltyProgram.user_id == user_id,
                LoyaltyProgram.deleted_at.is_(None),
            )
            .first()
        )

    def create(
        self,
        db: Session,
        user_id: int,
        *,
        organization_name: str,
        stamps_required: int = 10,
        reward_label: str | None = None,
        description: str | None = None,
        default_change_message: str | None = None,
        logo_url: str | None = None,
        background_color: str | None = None,
        foreground_color: str | None = None,
        label_color: str | None = None,
    ) -> LoyaltyProgram:
        """Create a draft program and mint its public enrollment token.

        Args:
            db: Database session.
            user_id: Operator who owns the program.
            organization_name: Merchant name shown on the card.
            stamps_required: Stamps that unlock the reward.
            reward_label: What the customer earns.
            description: Optional internal note.
            default_change_message: Lock-screen text (with ``%@``) pushed on a stamp.
            logo_url: Merchant logo baked onto the card.
            background_color: Card background color (rgb()/hex string).
            foreground_color: Card text color.
            label_color: Card label color.

        Returns:
            The persisted program, with a public token.
        """
        program = LoyaltyProgram(
            user_id=user_id,
            organization_name=organization_name,
            stamps_required=stamps_required,
            reward_label=reward_label,
            description=description,
            default_change_message=default_change_message,
            logo_url=logo_url,
            background_color=background_color,
            foreground_color=foreground_color,
            label_color=label_color,
            status=LoyaltyProgramStatus.DRAFT.value,
        )
        db.add(program)
        db.commit()
        db.refresh(program)
        wallet_enrollment_service.ensure_public_token(db, program)
        db.refresh(program)
        return program

    def update(self, db: Session, user_id: int, program_id: int, changes: dict[str, object]) -> LoyaltyProgram:
        """Apply an operator's edits to one of their programs.

        Only whitelisted config fields (plus ``status``) are writable; unknown keys are ignored.

        Args:
            db: Database session.
            user_id: Operator who must own the program.
            program_id: The program to update.
            changes: The fields to set (already narrowed to the ones the caller sent).

        Returns:
            The updated program.

        Raises:
            WalletProgramError: When the program is not found, or a status value is invalid.
        """
        program = self.get_for_user(db, user_id, program_id)
        if program is None:
            raise WalletProgramError("Programme introuvable")

        for field in _EDITABLE_FIELDS:
            if field in changes:
                setattr(program, field, changes[field])

        if "status" in changes:
            program.status = self._validated_status(changes["status"])

        db.commit()
        db.refresh(program)
        return program

    @staticmethod
    def _validated_status(value: object) -> str:
        """Return a valid program status string, or raise.

        Args:
            value: The candidate status.

        Returns:
            The validated status value.

        Raises:
            WalletProgramError: When the value is not a known status.
        """
        try:
            return LoyaltyProgramStatus(value).value
        except ValueError as error:
            raise WalletProgramError("Statut de programme invalide") from error


wallet_program_service = WalletProgramService()
