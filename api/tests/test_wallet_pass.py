"""Unit tests for the Apple Wallet pass service — pass.json, signed bundle, end-to-end."""

from __future__ import annotations

import datetime
import hashlib
import json
import zipfile
from io import BytesIO

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography.x509.oid import NameOID
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from models.loyalty_card import LoyaltyCard
from models.loyalty_program import LoyaltyProgram
from models.wallet_credentials import WalletCredentials
from services.wallet_credentials_service import WalletSigningMaterial, wallet_credentials_service
from services.wallet_pass_service import WalletPassError, wallet_pass_service

_WEB_SERVICE_URL = "https://api.example.fr/api/v1/wallet"


def _self_signed_pem(common_name: str) -> tuple[str, str]:
    """Generate a throwaway self-signed RSA certificate and its private key (PEM)."""
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
def signing_material() -> WalletSigningMaterial:
    """Real signing material (self-signed) so the PKCS#7 signature actually builds."""
    cert_pem, key_pem = _self_signed_pem("Test Pass Signer")
    wwdr_pem, _ = _self_signed_pem("Test WWDR")
    return WalletSigningMaterial(
        pass_type_identifier="pass.fr.dibodev.fidelite",
        team_id="TEAM123456",
        signing_certificate=cert_pem,
        signing_private_key=key_pem,
        wwdr_certificate=wwdr_pem,
    )


def _program() -> LoyaltyProgram:
    """A program with mixed color formats to exercise normalization."""
    return LoyaltyProgram(
        user_id=1,
        organization_name="Kebab Istanbul",
        stamps_required=10,
        reward_label="1 kebab offert",
        default_change_message="Plus que %@ avant votre kebab offert 🥙",
        background_color="rgb(20,20,20)",
        foreground_color="#ffffff",
    )


def _card() -> LoyaltyCard:
    """An in-progress card (3 stamps)."""
    return LoyaltyCard(program_id=1, user_id=1, serial_number="card-0001", stamps=3, authentication_token="a" * 16)


def test_pass_json_carries_store_card_and_identifiers(signing_material: WalletSigningMaterial) -> None:
    """The store card exposes the stamps, barcode, identifiers and normalized colors."""
    pass_json = wallet_pass_service.build_pass_json(
        _program(), _card(), signing_material, web_service_url=_WEB_SERVICE_URL
    )
    assert pass_json["passTypeIdentifier"] == "pass.fr.dibodev.fidelite"
    assert pass_json["teamIdentifier"] == "TEAM123456"
    assert pass_json["serialNumber"] == "card-0001"
    assert pass_json["authenticationToken"] == "a" * 16
    assert pass_json["webServiceURL"] == _WEB_SERVICE_URL
    assert pass_json["barcodes"][0]["message"] == "card-0001"
    assert pass_json["backgroundColor"] == "rgb(20, 20, 20)"
    assert pass_json["foregroundColor"] == "rgb(255, 255, 255)"
    primary = pass_json["storeCard"]["primaryFields"][0]
    assert primary["value"] == "3 / 10"
    assert "%@" in primary["changeMessage"]


def test_pkpass_is_a_valid_signed_bundle(signing_material: WalletSigningMaterial) -> None:
    """The archive holds pass.json, an icon, a matching manifest, and a chained signature."""
    pkpass = wallet_pass_service.build_pkpass(_program(), _card(), signing_material, web_service_url=_WEB_SERVICE_URL)
    with zipfile.ZipFile(BytesIO(pkpass)) as archive:
        names = set(archive.namelist())
        assert {"pass.json", "manifest.json", "signature", "icon.png"} <= names
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["pass.json"] == hashlib.sha1(archive.read("pass.json")).hexdigest()
        assert manifest["icon.png"] == hashlib.sha1(archive.read("icon.png")).hexdigest()
        signature = archive.read("signature")
    certificates = pkcs7.load_der_pkcs7_certificates(signature)
    assert len(certificates) == 2  # signer + WWDR chain embedded


def _memory_session() -> Session:
    """An in-memory SQLite session with the program/card/credentials tables."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(
        engine,
        tables=[LoyaltyProgram.__table__, LoyaltyCard.__table__, WalletCredentials.__table__],
    )
    return sessionmaker(bind=engine)()


def test_generate_for_card_end_to_end(signing_material: WalletSigningMaterial) -> None:
    """Stored (encrypted) credentials + a card produce a signed pass — A1↔A2↔A3."""
    db = _memory_session()
    try:
        wallet_credentials_service.save_for_user(
            db,
            1,
            pass_type_identifier=signing_material.pass_type_identifier,
            team_id=signing_material.team_id,
            apns_key_id="KEY1234567",
            signing_certificate=signing_material.signing_certificate,
            signing_private_key=signing_material.signing_private_key,
            wwdr_certificate=signing_material.wwdr_certificate,
            apns_auth_key="-----BEGIN PRIVATE KEY-----p8-----END PRIVATE KEY-----",
        )
        program = _program()
        db.add(program)
        db.flush()
        card = LoyaltyCard(
            program_id=program.id, user_id=1, serial_number="card-e2e", stamps=1, authentication_token="b" * 16
        )
        db.add(card)
        db.flush()

        pkpass = wallet_pass_service.generate_for_card(db, 1, card.id)

        with zipfile.ZipFile(BytesIO(pkpass)) as archive:
            assert "signature" in archive.namelist()
            assert json.loads(archive.read("pass.json"))["serialNumber"] == "card-e2e"
    finally:
        db.close()


def test_generate_for_card_raises_without_card(signing_material: WalletSigningMaterial) -> None:
    """A missing card fails loudly rather than producing an empty pass."""
    db = _memory_session()
    try:
        with pytest.raises(WalletPassError):
            wallet_pass_service.generate_for_card(db, 1, 999)
    finally:
        db.close()
