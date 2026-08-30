"""Unit tests for the Apple Wallet credentials service — encryption at rest + loud failure."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from models.wallet_credentials import WalletCredentials
from services import wallet_credentials_service as wcs


@pytest.fixture
def session() -> Iterator[Session]:
    """A session on an isolated in-memory SQLite holding only the credentials table."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[WalletCredentials.__table__])
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _full_material() -> dict[str, str]:
    """A complete set of placeholder Apple credentials."""
    return {
        "pass_type_identifier": "pass.fr.dibodev.fidelite",
        "team_id": "TEAM123456",
        "apns_key_id": "KEY1234567",
        "signing_certificate": "-----BEGIN CERTIFICATE-----cert-----END CERTIFICATE-----",
        "signing_private_key": "-----BEGIN PRIVATE KEY-----key-----END PRIVATE KEY-----",
        "wwdr_certificate": "-----BEGIN CERTIFICATE-----wwdr-----END CERTIFICATE-----",
        "apns_auth_key": "-----BEGIN PRIVATE KEY-----p8-----END PRIVATE KEY-----",
    }


def test_secrets_are_encrypted_at_rest(session: Session) -> None:
    """Stored secret columns hold ciphertext, never the plaintext that was passed in."""
    material = _full_material()
    record = wcs.wallet_credentials_service.save_for_user(session, 1, **material)
    assert record.is_active is True
    assert record.signing_private_key not in ("", material["signing_private_key"])
    assert record.apns_auth_key not in ("", material["apns_auth_key"])


def test_signing_material_round_trips(session: Session) -> None:
    """The signing material decrypts back to exactly what was stored."""
    material = _full_material()
    wcs.wallet_credentials_service.save_for_user(session, 1, **material)
    signing = wcs.wallet_credentials_service.require_signing_material(session, 1)
    assert signing.signing_certificate == material["signing_certificate"]
    assert signing.signing_private_key == material["signing_private_key"]
    assert signing.wwdr_certificate == material["wwdr_certificate"]
    assert signing.pass_type_identifier == material["pass_type_identifier"]
    assert signing.team_id == material["team_id"]


def test_apns_material_round_trips(session: Session) -> None:
    """The APNs material decrypts back with its identifiers."""
    wcs.wallet_credentials_service.save_for_user(session, 1, **_full_material())
    apns = wcs.wallet_credentials_service.require_apns_material(session, 1)
    assert apns.key_id == "KEY1234567"
    assert apns.auth_key.startswith("-----BEGIN PRIVATE KEY-----")
    assert apns.pass_type_identifier == "pass.fr.dibodev.fidelite"


def test_require_raises_without_credentials(session: Session) -> None:
    """Asking for material a user never stored fails loudly, never silently."""
    with pytest.raises(wcs.WalletCredentialsMissingError):
        wcs.wallet_credentials_service.require_signing_material(session, 999)


def test_require_signing_raises_when_a_secret_is_missing(session: Session) -> None:
    """A partial credential set is not usable — the missing piece is named."""
    material = _full_material() | {"wwdr_certificate": ""}
    record = wcs.wallet_credentials_service.save_for_user(session, 1, **material)
    assert record.is_active is False
    with pytest.raises(wcs.WalletCredentialsMissingError, match="wwdr_certificate"):
        wcs.wallet_credentials_service.require_signing_material(session, 1)


def test_bootstrap_from_settings_seeds_then_noops(session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    """A full env-provided set seeds the credentials once, then bootstrap is a no-op."""
    for name, value in _full_material().items():
        monkeypatch.setattr(wcs.settings, f"wallet_{name}", value, raising=False)
    seeded = wcs.wallet_credentials_service.bootstrap_from_settings(session, 1)
    assert seeded is not None
    assert seeded.is_active is True
    assert wcs.wallet_credentials_service.bootstrap_from_settings(session, 1) is None


def test_bootstrap_from_settings_skips_when_incomplete(session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    """An incomplete env set seeds nothing rather than storing a half credential."""
    material = _full_material() | {"apns_auth_key": ""}
    for name, value in material.items():
        monkeypatch.setattr(wcs.settings, f"wallet_{name}", value, raising=False)
    assert wcs.wallet_credentials_service.bootstrap_from_settings(session, 2) is None
    assert wcs.wallet_credentials_service.get_for_user(session, 2) is None
