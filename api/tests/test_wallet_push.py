"""Unit tests for the Apple Wallet push service — provider JWT, request shape, pruning."""

from __future__ import annotations

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from models.wallet_credentials import WalletCredentials
from models.wallet_device_registration import WalletDeviceRegistration
from services.wallet_credentials_service import (
    WalletApnsMaterial,
    WalletCredentialsMissingError,
    wallet_credentials_service,
)
from services.wallet_push_service import WalletPushService


def _p8_key_pem() -> str:
    """Generate a throwaway EC P-256 private key (PEM) standing in for the .p8 APNs key."""
    key = ec.generate_private_key(ec.SECP256R1())
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")


def _apns_material() -> tuple[WalletApnsMaterial, str]:
    """Build APNs material plus the matching public key PEM to verify the JWT."""
    key = ec.generate_private_key(ec.SECP256R1())
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = (
        key.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    material = WalletApnsMaterial(
        pass_type_identifier="pass.fr.dibodev.fidelite",
        team_id="TEAM123456",
        key_id="KEY1234567",
        auth_key=private_pem,
    )
    return material, public_pem


def test_push_sends_bearer_jwt_topic_and_empty_body() -> None:
    """The request targets the device, carries the topic, an ES256 bearer JWT and ``{}``."""
    material, public_pem = _apns_material()
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["authorization"] = request.headers.get("authorization")
        captured["topic"] = request.headers.get("apns-topic")
        captured["body"] = request.content
        return httpx.Response(200)

    service = WalletPushService(transport=httpx.MockTransport(handler))
    result = service.push_to_token("device-token-1", apns_material=material)

    assert result.status_code == 200
    assert result.is_unregistered is False
    assert captured["path"] == "/3/device/device-token-1"
    assert captured["topic"] == "pass.fr.dibodev.fidelite"
    assert captured["body"] == b"{}"

    scheme, _, token = str(captured["authorization"]).partition(" ")
    assert scheme == "bearer"
    assert jwt.get_unverified_header(token)["kid"] == "KEY1234567"
    payload = jwt.decode(token, public_pem, algorithms=["ES256"])
    assert payload["iss"] == "TEAM123456"


def test_provider_token_is_reused_across_pushes() -> None:
    """A second push within the refresh window reuses the same provider token."""
    material, _ = _apns_material()
    tokens: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        tokens.append(str(request.headers.get("authorization")))
        return httpx.Response(200)

    service = WalletPushService(transport=httpx.MockTransport(handler))
    service.push_to_token("device-a", apns_material=material)
    service.push_to_token("device-b", apns_material=material)
    assert tokens[0] == tokens[1]


def test_push_reports_unregistered_on_410() -> None:
    """A 410 marks the token as unregistered so the caller can forget it."""
    material, _ = _apns_material()
    service = WalletPushService(transport=httpx.MockTransport(lambda request: httpx.Response(410)))
    result = service.push_to_token("dead-token", apns_material=material)
    assert result.status_code == 410
    assert result.is_unregistered is True


def test_push_card_update_prunes_unregistered_devices() -> None:
    """Pushing a card wakes each device and drops the ones APNs reports as gone."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[WalletCredentials.__table__, WalletDeviceRegistration.__table__])
    db = sessionmaker(bind=engine)()
    try:
        wallet_credentials_service.save_for_user(
            db,
            1,
            pass_type_identifier="pass.fr.dibodev.fidelite",
            team_id="TEAM123456",
            apns_key_id="KEY1234567",
            signing_certificate="cert",
            signing_private_key="key",
            wwdr_certificate="wwdr",
            apns_auth_key=_p8_key_pem(),
        )
        for token in ("live-token", "dead-token"):
            db.add(
                WalletDeviceRegistration(
                    card_id=5,
                    user_id=1,
                    device_library_identifier=f"device-{token}",
                    push_token=token,
                    pass_type_identifier="pass.fr.dibodev.fidelite",
                    serial_number="card-5",
                )
            )
        db.commit()

        def handler(request: httpx.Request) -> httpx.Response:
            token = request.url.path.rsplit("/", 1)[-1]
            return httpx.Response(410 if token == "dead-token" else 200)

        service = WalletPushService(transport=httpx.MockTransport(handler))
        results = service.push_card_update(db, 1, 5)

        assert {result.status_code for result in results} == {200, 410}
        remaining = db.query(WalletDeviceRegistration).all()
        assert [registration.push_token for registration in remaining] == ["live-token"]
    finally:
        db.close()
        engine.dispose()


def test_push_card_update_requires_apns_material() -> None:
    """Without stored APNs credentials the push fails loudly instead of silently."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[WalletCredentials.__table__, WalletDeviceRegistration.__table__])
    db = sessionmaker(bind=engine)()
    try:
        with pytest.raises(WalletCredentialsMissingError):
            WalletPushService().push_card_update(db, 1, 5)
    finally:
        db.close()
        engine.dispose()
