"""Wallet PassKit service — the device-facing protocol (registration + updates).

Implements the logic Apple's device calls once a pass is added: register/unregister a
device's push token, list the serials that changed, and authenticate a request against
the pass's ``authenticationToken``. HTTP shaping lives in the ``wallet`` route; this
service holds the testable protocol logic.
"""

from __future__ import annotations

import hmac
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from enums.wallet_registration_outcome import WalletRegistrationOutcome
from models.loyalty_card import LoyaltyCard
from models.wallet_device_registration import WalletDeviceRegistration

_APPLE_PASS_SCHEME = "ApplePass"


class WalletPassKitService:
    """Device registration, update discovery, and pass-token authentication."""

    @staticmethod
    def parse_pass_token(authorization_header: str | None) -> str | None:
        """Extract the pass token from an ``Authorization: ApplePass <token>`` header.

        Args:
            authorization_header: Raw header value, or ``None``.

        Returns:
            The token, or ``None`` when the header is absent or malformed.
        """
        if not authorization_header:
            return None
        scheme, _, token = authorization_header.partition(" ")
        if scheme != _APPLE_PASS_SCHEME or not token.strip():
            return None
        return token.strip()

    def authenticated_card(self, db: Session, *, serial_number: str, pass_token: str | None) -> LoyaltyCard | None:
        """Return the card iff the pass token matches its ``authentication_token``.

        Args:
            db: Database session.
            serial_number: Pass serial from the request path.
            pass_token: Token parsed from the Authorization header.

        Returns:
            The authenticated card, or ``None`` (unknown serial or wrong token).
        """
        if not pass_token:
            return None
        card = db.query(LoyaltyCard).filter(LoyaltyCard.serial_number == serial_number).first()
        if card is None:
            return None
        if not hmac.compare_digest(card.authentication_token or "", pass_token):
            return None
        return card

    def register_device(
        self,
        db: Session,
        *,
        device_library_identifier: str,
        pass_type_identifier: str,
        serial_number: str,
        push_token: str,
        pass_token: str | None,
    ) -> WalletRegistrationOutcome:
        """Register (or refresh) a device's push token for a pass.

        Args:
            db: Database session.
            device_library_identifier: Apple's per-device identifier.
            pass_type_identifier: Pass type id from the request path.
            serial_number: Pass serial from the request path.
            push_token: The device's APNs token.
            pass_token: Token parsed from the Authorization header.

        Returns:
            The registration outcome.
        """
        card = self.authenticated_card(db, serial_number=serial_number, pass_token=pass_token)
        if card is None:
            return WalletRegistrationOutcome.UNAUTHORIZED
        existing = (
            db.query(WalletDeviceRegistration)
            .filter(
                WalletDeviceRegistration.device_library_identifier == device_library_identifier,
                WalletDeviceRegistration.serial_number == serial_number,
            )
            .first()
        )
        if existing is not None:
            existing.push_token = push_token
            db.commit()
            return WalletRegistrationOutcome.ALREADY_REGISTERED
        db.add(
            WalletDeviceRegistration(
                card_id=card.id,
                user_id=card.user_id,
                device_library_identifier=device_library_identifier,
                push_token=push_token,
                pass_type_identifier=pass_type_identifier,
                serial_number=serial_number,
            )
        )
        if card.added_to_wallet_at is None:
            card.added_to_wallet_at = datetime.now(UTC).replace(tzinfo=None)
        db.commit()
        return WalletRegistrationOutcome.CREATED

    def unregister_device(
        self, db: Session, *, device_library_identifier: str, serial_number: str, pass_token: str | None
    ) -> WalletRegistrationOutcome:
        """Unregister a device from a pass (idempotent once authenticated).

        Args:
            db: Database session.
            device_library_identifier: Apple's per-device identifier.
            serial_number: Pass serial from the request path.
            pass_token: Token parsed from the Authorization header.

        Returns:
            ``DELETED`` once authenticated, ``UNAUTHORIZED`` otherwise.
        """
        card = self.authenticated_card(db, serial_number=serial_number, pass_token=pass_token)
        if card is None:
            return WalletRegistrationOutcome.UNAUTHORIZED
        registration = (
            db.query(WalletDeviceRegistration)
            .filter(
                WalletDeviceRegistration.device_library_identifier == device_library_identifier,
                WalletDeviceRegistration.serial_number == serial_number,
            )
            .first()
        )
        if registration is not None:
            db.delete(registration)
            db.commit()
        return WalletRegistrationOutcome.DELETED

    def serials_updated_since(
        self, db: Session, *, device_library_identifier: str, pass_type_identifier: str, updated_since: str | None
    ) -> tuple[list[str], str | None]:
        """List the serials of a device's passes that changed after ``updated_since``.

        Args:
            db: Database session.
            device_library_identifier: Apple's per-device identifier.
            pass_type_identifier: Pass type id from the request path.
            updated_since: Opaque tag the device last stored (a unix timestamp string).

        Returns:
            The changed serials and the newest change tag (both empty/None when the
            device has no registrations).
        """
        registrations = (
            db.query(WalletDeviceRegistration)
            .filter(
                WalletDeviceRegistration.device_library_identifier == device_library_identifier,
                WalletDeviceRegistration.pass_type_identifier == pass_type_identifier,
            )
            .all()
        )
        if not registrations:
            return [], None
        serials = [registration.serial_number for registration in registrations]
        cards = db.query(LoyaltyCard).filter(LoyaltyCard.serial_number.in_(serials)).all()
        since = int(updated_since) if updated_since and updated_since.isdigit() else None
        changed: list[str] = []
        latest = 0
        for card in cards:
            tag = self._change_tag(card)
            latest = max(latest, tag)
            if since is None or tag > since:
                changed.append(card.serial_number)
        return changed, str(latest)

    @staticmethod
    def _change_tag(card: LoyaltyCard) -> int:
        """Unix-timestamp tag of a card's last change (updated_at, else created_at)."""
        moment = card.updated_at or card.created_at
        return int(moment.replace(tzinfo=UTC).timestamp())


wallet_passkit_service = WalletPassKitService()
