"""Unit tests for the Apple Wallet enrollment service — minting, idempotency, pkpass."""

from __future__ import annotations

import datetime
import zipfile
from collections.abc import Iterator
from io import BytesIO

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from models.loyalty_card import LoyaltyCard
from models.loyalty_program import LoyaltyProgram
from models.wallet_credentials import WalletCredentials
from services.wallet_credentials_service import wallet_credentials_service
from services.wallet_enrollment_service import WalletEnrollmentError, wallet_enrollment_service


def _self_signed(common_name: str) -> tuple[str, str]:
    """Generate a throwaway self-signed RSA certificate and private key (PEM)."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode("utf-8")
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")
    return cert_pem, key_pem


@pytest.fixture(scope="module")
def signing_pems() -> tuple[str, str, str]:
    """Reusable self-signed signing material so the pkpass actually builds."""
    cert_pem, key_pem = _self_signed("Signer")
    wwdr_pem, _ = _self_signed("WWDR")
    return cert_pem, key_pem, wwdr_pem


@pytest.fixture
def session() -> Iterator[Session]:
    """A session on an isolated in-memory SQLite with the program/card/credentials tables."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(
        engine,
        tables=[LoyaltyProgram.__table__, LoyaltyCard.__table__, WalletCredentials.__table__],
    )
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _store_credentials(db: Session, signing_pems: tuple[str, str, str]) -> None:
    """Persist encrypted signing credentials for user 1."""
    cert_pem, key_pem, wwdr_pem = signing_pems
    wallet_credentials_service.save_for_user(
        db,
        1,
        pass_type_identifier="pass.fr.dibodev.fidelite",
        team_id="TEAM123456",
        apns_key_id="KEY1234567",
        signing_certificate=cert_pem,
        signing_private_key=key_pem,
        wwdr_certificate=wwdr_pem,
        apns_auth_key="-----BEGIN PRIVATE KEY-----p8-----END PRIVATE KEY-----",
    )


def _program(db: Session, *, public_token: str = "tok-public") -> LoyaltyProgram:
    """Persist a program exposed under a public token."""
    program = LoyaltyProgram(
        user_id=1, organization_name="Kebab Istanbul", stamps_required=10, public_token=public_token
    )
    db.add(program)
    db.flush()
    return program


def test_ensure_public_token_generates_and_is_idempotent(session: Session) -> None:
    """A program without a public token gets one, and a second call returns the same."""
    program = LoyaltyProgram(user_id=1, organization_name="Café Central")
    session.add(program)
    session.flush()
    token = wallet_enrollment_service.ensure_public_token(session, program)
    assert token
    assert wallet_enrollment_service.ensure_public_token(session, program) == token


def test_add_card_mints_and_returns_a_signed_pkpass(session: Session, signing_pems: tuple[str, str, str]) -> None:
    """Enrollment mints a card with a serial + token and returns a signed pass."""
    _store_credentials(session, signing_pems)
    _program(session)
    session.commit()

    card, pkpass = wallet_enrollment_service.add_card(
        session, public_token="tok-public", holder_email="alice@example.fr", consent=True
    )
    assert card.serial_number
    assert card.authentication_token
    assert card.marketing_consent_at is not None
    with zipfile.ZipFile(BytesIO(pkpass)) as archive:
        assert {"pass.json", "signature"} <= set(archive.namelist())


def test_add_card_is_idempotent_by_email(session: Session, signing_pems: tuple[str, str, str]) -> None:
    """The same email reuses the customer's card; a new email mints a new one."""
    _store_credentials(session, signing_pems)
    _program(session)
    session.commit()

    first, _ = wallet_enrollment_service.add_card(session, public_token="tok-public", holder_email="alice@example.fr")
    second, _ = wallet_enrollment_service.add_card(session, public_token="tok-public", holder_email="alice@example.fr")
    assert first.id == second.id
    assert session.query(LoyaltyCard).count() == 1

    third, _ = wallet_enrollment_service.add_card(session, public_token="tok-public", holder_email="bob@example.fr")
    assert third.id != first.id
    assert session.query(LoyaltyCard).count() == 2


def test_add_card_without_email_mints_each_time(session: Session, signing_pems: tuple[str, str, str]) -> None:
    """Anonymous adds cannot be de-duplicated, so each one mints a fresh card."""
    _store_credentials(session, signing_pems)
    _program(session)
    session.commit()

    first, _ = wallet_enrollment_service.add_card(session, public_token="tok-public")
    second, _ = wallet_enrollment_service.add_card(session, public_token="tok-public")
    assert first.id != second.id
    assert session.query(LoyaltyCard).count() == 2


def test_add_card_unknown_token_raises(session: Session) -> None:
    """An unknown public token fails loudly rather than minting an orphan card."""
    with pytest.raises(WalletEnrollmentError):
        wallet_enrollment_service.add_card(session, public_token="does-not-exist")


def test_get_public_program_resolves_only_live_tokens(session: Session) -> None:
    """A live token resolves its program; unknown or soft-deleted tokens resolve to None."""
    program = _program(session)
    session.commit()

    assert wallet_enrollment_service.get_public_program(session, "tok-public") is not None
    assert wallet_enrollment_service.get_public_program(session, "unknown") is None

    program.deleted_at = datetime.datetime(2026, 1, 1)
    session.commit()
    assert wallet_enrollment_service.get_public_program(session, "tok-public") is None
