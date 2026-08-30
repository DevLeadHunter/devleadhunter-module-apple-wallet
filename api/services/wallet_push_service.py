"""Wallet push service — wake iPhones over APNs so they re-fetch an updated pass.

The push carries an empty payload ``{}``: it does not transport a message, it only tells
the device to call the PassKit web service again. The lock-screen text the customer sees
is the ``changeMessage`` of the card field that changed. Auth is a token-based APNs
provider JWT (ES256, from the ``.p8`` key) — no ``aioapns``/``apns2`` dependency.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
import jwt
from sqlalchemy.orm import Session

from models.wallet_device_registration import WalletDeviceRegistration
from services.wallet_credentials_service import WalletApnsMaterial, wallet_credentials_service

_APNS_HOST_PRODUCTION = "https://api.push.apple.com"
_APNS_HOST_SANDBOX = "https://api.sandbox.push.apple.com"
# Apple accepts a provider token for up to 1h and rate-limits token minting; refresh under that.
_TOKEN_REFRESH_SECONDS = 50 * 60
_UNREGISTERED_STATUS = 410
_REQUEST_TIMEOUT_SECONDS = 10.0


class WalletPushError(RuntimeError):
    """Raised when a push cannot even be attempted (e.g. an unusable APNs key)."""


@dataclass(frozen=True)
class WalletPushResult:
    """Outcome of a single device push."""

    push_token: str
    status_code: int
    is_unregistered: bool  # 410 → the device dropped the pass; its token must be forgotten


class WalletPushService:
    """Sends empty APNs pushes to a card's registered devices, token-based auth."""

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        """Initialize the service.

        Args:
            transport: Optional httpx transport, injected in tests to stub APNs.
        """
        self._transport = transport
        self._token_cache: dict[tuple[str, str], tuple[str, float]] = {}

    def push_card_update(
        self, db: Session, user_id: int, card_id: int, *, sandbox: bool = False
    ) -> list[WalletPushResult]:
        """Push an update to every device registered for a card, pruning dead tokens.

        Args:
            db: Database session.
            user_id: Operator who owns the card and the APNs credentials.
            card_id: Card whose devices to wake.
            sandbox: Target the APNs sandbox host instead of production.

        Returns:
            One result per device pushed.

        Raises:
            WalletCredentialsMissingError: When the APNs material is absent.
        """
        apns_material = wallet_credentials_service.require_apns_material(db, user_id)
        registrations = (
            db.query(WalletDeviceRegistration)
            .filter(WalletDeviceRegistration.card_id == card_id, WalletDeviceRegistration.user_id == user_id)
            .all()
        )
        results = [
            self.push_to_token(registration.push_token, apns_material=apns_material, sandbox=sandbox)
            for registration in registrations
        ]
        pruned = False
        for registration, result in zip(registrations, results, strict=True):
            if result.is_unregistered:
                db.delete(registration)
                pruned = True
        if pruned:
            db.commit()
        return results

    def push_to_token(
        self, push_token: str, *, apns_material: WalletApnsMaterial, sandbox: bool = False
    ) -> WalletPushResult:
        """Send one empty APNs push to a device token.

        Args:
            push_token: The device's APNs token for this pass.
            apns_material: Decrypted APNs credentials (topic, team, key).
            sandbox: Target the APNs sandbox host instead of production.

        Returns:
            The push outcome.
        """
        provider_token = self._provider_token(apns_material)
        host = _APNS_HOST_SANDBOX if sandbox else _APNS_HOST_PRODUCTION
        headers = {
            "authorization": f"bearer {provider_token}",
            "apns-topic": apns_material.pass_type_identifier,
        }
        with self._client() as client:
            response = client.post(f"{host}/3/device/{push_token}", headers=headers, content=b"{}")
        return WalletPushResult(push_token, response.status_code, response.status_code == _UNREGISTERED_STATUS)

    def _client(self) -> httpx.Client:
        """Build the httpx client — HTTP/2 in production, the injected transport in tests."""
        if self._transport is not None:
            return httpx.Client(transport=self._transport, timeout=_REQUEST_TIMEOUT_SECONDS)
        return httpx.Client(http2=True, timeout=_REQUEST_TIMEOUT_SECONDS)

    def _provider_token(self, apns_material: WalletApnsMaterial) -> str:
        """Return a cached provider JWT, minting a fresh one when the cache is stale."""
        cache_key = (apns_material.team_id, apns_material.key_id)
        cached = self._token_cache.get(cache_key)
        now = time.time()
        if cached is not None and now - cached[1] < _TOKEN_REFRESH_SECONDS:
            return cached[0]
        token = self._build_provider_token(apns_material, now)
        self._token_cache[cache_key] = (token, now)
        return token

    @staticmethod
    def _build_provider_token(apns_material: WalletApnsMaterial, issued_at: float) -> str:
        """Sign an ES256 APNs provider JWT with the ``.p8`` key.

        Args:
            apns_material: Decrypted APNs credentials.
            issued_at: Unix timestamp for the ``iat`` claim.

        Returns:
            The encoded JWT.

        Raises:
            WalletPushError: When the key cannot sign the token.
        """
        try:
            return jwt.encode(
                {"iss": apns_material.team_id, "iat": int(issued_at)},
                apns_material.auth_key,
                algorithm="ES256",
                headers={"kid": apns_material.key_id},
            )
        except Exception as error:
            raise WalletPushError(f"Failed to build APNs provider token: {error}") from error


wallet_push_service = WalletPushService()
