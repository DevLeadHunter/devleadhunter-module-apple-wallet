"""Wallet credentials service — securely store and retrieve the Apple signing/APNs material.

Never fails silently: retrieving material for signing a ``.pkpass`` or pushing an APNs
update raises :class:`WalletCredentialsMissingError` when anything is absent, the same
loud-failure contract as the payment providers.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from core.config import settings
from models.wallet_credentials import WalletCredentials
from services.encryption_service import encryption_service


class WalletCredentialsMissingError(RuntimeError):
    """Raised when required Apple Wallet credentials are absent — never fail silently."""


@dataclass(frozen=True)
class WalletSigningMaterial:
    """Decrypted material needed to sign a ``.pkpass``."""

    pass_type_identifier: str
    team_id: str
    signing_certificate: str
    signing_private_key: str
    wwdr_certificate: str


@dataclass(frozen=True)
class WalletApnsMaterial:
    """Decrypted material needed to push a pass update over APNs."""

    pass_type_identifier: str
    team_id: str
    key_id: str
    auth_key: str


class WalletCredentialsService:
    """Stores and retrieves a user's Apple Wallet credentials, encrypted at rest."""

    def get_for_user(self, db: Session, user_id: int) -> WalletCredentials | None:
        """Return the stored credentials for a user, or ``None`` when absent.

        Args:
            db: Database session.
            user_id: Operator who owns the credentials.

        Returns:
            The stored row, or ``None``.
        """
        return db.query(WalletCredentials).filter(WalletCredentials.user_id == user_id).first()

    def save_for_user(
        self,
        db: Session,
        user_id: int,
        *,
        pass_type_identifier: str,
        team_id: str,
        apns_key_id: str,
        signing_certificate: str,
        signing_private_key: str,
        wwdr_certificate: str,
        apns_auth_key: str,
    ) -> WalletCredentials:
        """Encrypt the secret material and upsert the user's credentials.

        Args:
            db: Database session.
            user_id: Operator who owns the credentials.
            pass_type_identifier: Apple Pass Type ID.
            team_id: Apple Developer Team ID.
            apns_key_id: Key ID of the ``.p8`` APNs key.
            signing_certificate: Pass signing certificate (PEM).
            signing_private_key: Private signing key (PEM).
            wwdr_certificate: Apple WWDR intermediate certificate (PEM).
            apns_auth_key: ``.p8`` APNs auth key.

        Returns:
            The persisted credentials row.
        """
        record = self.get_for_user(db, user_id) or WalletCredentials(user_id=user_id)
        record.pass_type_identifier = pass_type_identifier
        record.team_id = team_id
        record.apns_key_id = apns_key_id
        record.signing_certificate = self._encrypt(signing_certificate)
        record.signing_private_key = self._encrypt(signing_private_key)
        record.wwdr_certificate = self._encrypt(wwdr_certificate)
        record.apns_auth_key = self._encrypt(apns_auth_key)
        record.is_active = all(
            (
                pass_type_identifier,
                team_id,
                apns_key_id,
                signing_certificate,
                signing_private_key,
                wwdr_certificate,
                apns_auth_key,
            )
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def bootstrap_from_settings(self, db: Session, user_id: int) -> WalletCredentials | None:
        """Seed a user's credentials from env settings when a full set is present and none stored.

        Lets a deployment inject the material through GitHub secrets → ``.env``.
        No-op (returns ``None``) when credentials already exist or the settings are incomplete.

        Args:
            db: Database session.
            user_id: Operator to seed the credentials for.

        Returns:
            The seeded credentials row, or ``None`` when nothing was seeded.
        """
        if self.get_for_user(db, user_id) is not None:
            return None
        settings_material = (
            settings.wallet_pass_type_identifier,
            settings.wallet_team_id,
            settings.wallet_apns_key_id,
            settings.wallet_signing_certificate,
            settings.wallet_signing_private_key,
            settings.wallet_wwdr_certificate,
            settings.wallet_apns_auth_key,
        )
        if not all(settings_material):
            return None
        return self.save_for_user(
            db,
            user_id,
            pass_type_identifier=settings.wallet_pass_type_identifier,
            team_id=settings.wallet_team_id,
            apns_key_id=settings.wallet_apns_key_id,
            signing_certificate=settings.wallet_signing_certificate,
            signing_private_key=settings.wallet_signing_private_key,
            wwdr_certificate=settings.wallet_wwdr_certificate,
            apns_auth_key=settings.wallet_apns_auth_key,
        )

    def require_signing_material(self, db: Session, user_id: int) -> WalletSigningMaterial:
        """Return the decrypted signing material, raising loudly when incomplete.

        Args:
            db: Database session.
            user_id: Operator who owns the credentials.

        Returns:
            The decrypted signing material.

        Raises:
            WalletCredentialsMissingError: When no row exists or a required piece is empty.
        """
        record = self._require_record(db, user_id)
        material = {
            "pass_type_identifier": record.pass_type_identifier or "",
            "team_id": record.team_id or "",
            "signing_certificate": self._decrypt(record.signing_certificate),
            "signing_private_key": self._decrypt(record.signing_private_key),
            "wwdr_certificate": self._decrypt(record.wwdr_certificate),
        }
        self._assert_complete(user_id, "signing", material)
        return WalletSigningMaterial(**material)

    def require_apns_material(self, db: Session, user_id: int) -> WalletApnsMaterial:
        """Return the decrypted APNs material, raising loudly when incomplete.

        Args:
            db: Database session.
            user_id: Operator who owns the credentials.

        Returns:
            The decrypted APNs material.

        Raises:
            WalletCredentialsMissingError: When no row exists or a required piece is empty.
        """
        record = self._require_record(db, user_id)
        material = {
            "pass_type_identifier": record.pass_type_identifier or "",
            "team_id": record.team_id or "",
            "key_id": record.apns_key_id or "",
            "auth_key": self._decrypt(record.apns_auth_key),
        }
        self._assert_complete(user_id, "APNs", material)
        return WalletApnsMaterial(**material)

    def _require_record(self, db: Session, user_id: int) -> WalletCredentials:
        """Return the credentials row or raise when the user has none."""
        record = self.get_for_user(db, user_id)
        if record is None:
            raise WalletCredentialsMissingError(f"No Apple Wallet credentials stored for user {user_id}.")
        return record

    @staticmethod
    def _assert_complete(user_id: int, kind: str, material: dict[str, str]) -> None:
        """Raise when any value in the decrypted material is empty."""
        missing = [name for name, value in material.items() if not value]
        if missing:
            raise WalletCredentialsMissingError(
                f"Incomplete Apple Wallet {kind} material for user {user_id}: missing {', '.join(missing)}."
            )

    @staticmethod
    def _encrypt(value: str) -> str:
        """Encrypt a value, tolerating an empty input."""
        return encryption_service.encrypt(value or "")

    @staticmethod
    def _decrypt(value: str | None) -> str:
        """Decrypt a stored value, returning an empty string when nothing is stored."""
        return encryption_service.decrypt(value) if value else ""


wallet_credentials_service = WalletCredentialsService()
