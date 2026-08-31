"""Wallet pass service — build and sign a ``.pkpass`` from a loyalty card.

A ``.pkpass`` is a zip of ``pass.json`` + images + ``manifest.json`` (SHA-1 of every
file, per the Apple spec) + ``signature`` (a detached PKCS#7 of the manifest, signed
with the pass certificate and chained to the Apple WWDR intermediate). Signing is done
in-process with ``cryptography`` — no external ``openssl`` binary.
"""

from __future__ import annotations

import hashlib
import json
import logging
import zipfile
from io import BytesIO

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography.x509 import load_pem_x509_certificate
from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

from core.config import settings
from models.loyalty_card import LoyaltyCard
from models.loyalty_program import LoyaltyProgram
from services.wallet_credentials_service import WalletSigningMaterial, wallet_credentials_service

logger = logging.getLogger(__name__)

_DEFAULT_BACKGROUND = (23, 23, 23)
_DEFAULT_FOREGROUND = (255, 255, 255)
_DEFAULT_LABEL = (200, 200, 200)
_ICON_SIZES = {"icon.png": 29, "icon@2x.png": 58, "icon@3x.png": 87}
# Apple logo slots (top of the pass): heights in pt × scale, widths capped so wide logos don't distort.
_LOGO_HEIGHTS = {"logo.png": 50, "logo@2x.png": 100, "logo@3x.png": 150}
_LOGO_MAX_WIDTHS = {"logo.png": 160, "logo@2x.png": 320, "logo@3x.png": 480}
_LOGO_FETCH_TIMEOUT_SECONDS = 5.0


class WalletPassError(RuntimeError):
    """Raised when a ``.pkpass`` cannot be built (e.g. a card with no program)."""


class WalletPassService:
    """Builds the ``pass.json``, renders icons, and signs the ``.pkpass`` bundle."""

    def generate_for_card(self, db: Session, user_id: int, card_id: int) -> bytes:
        """Build a signed ``.pkpass`` for one card, loading everything it needs.

        Args:
            db: Database session.
            user_id: Operator who owns the card and the signing credentials.
            card_id: Card to build the pass for.

        Returns:
            The signed ``.pkpass`` bytes.

        Raises:
            WalletPassError: When the card or its program is missing.
            WalletCredentialsMissingError: When signing material is absent.
        """
        card = db.query(LoyaltyCard).filter(LoyaltyCard.id == card_id, LoyaltyCard.user_id == user_id).first()
        if card is None:
            raise WalletPassError(f"No loyalty card {card_id} for user {user_id}.")
        program = db.query(LoyaltyProgram).filter(LoyaltyProgram.id == card.program_id).first()
        if program is None:
            raise WalletPassError(f"Loyalty card {card_id} has no program.")
        signing_material = wallet_credentials_service.require_signing_material(db, user_id)
        return self.build_pkpass(program, card, signing_material, web_service_url=self._web_service_url())

    def build_pkpass(
        self,
        program: LoyaltyProgram,
        card: LoyaltyCard,
        signing_material: WalletSigningMaterial,
        *,
        web_service_url: str,
        images: dict[str, bytes] | None = None,
    ) -> bytes:
        """Assemble and sign the full ``.pkpass`` archive.

        Args:
            program: The card's loyalty program (branding + stamp rules).
            card: The card being issued.
            signing_material: Decrypted Apple signing material.
            web_service_url: PassKit web-service base URL baked into the pass.
            images: Bundle images by filename; default icons are rendered when omitted.

        Returns:
            The signed ``.pkpass`` bytes.
        """
        pass_json = self.build_pass_json(program, card, signing_material, web_service_url=web_service_url)
        pass_bytes = self._to_bytes(pass_json)
        default_images = {**self.render_default_icons(program), **self._render_logo_images(program.logo_url)}
        bundle = {"pass.json": pass_bytes, **(images if images is not None else default_images)}
        manifest = self._build_manifest(bundle)
        signature = self._sign_manifest(manifest, signing_material)
        return self._zip({**bundle, "manifest.json": manifest, "signature": signature})

    def build_pass_json(
        self,
        program: LoyaltyProgram,
        card: LoyaltyCard,
        signing_material: WalletSigningMaterial,
        *,
        web_service_url: str,
    ) -> dict[str, object]:
        """Build the ``pass.json`` payload for a store card.

        Args:
            program: The card's loyalty program.
            card: The card being issued.
            signing_material: Provides the team + pass type identifiers.
            web_service_url: PassKit web-service base URL.

        Returns:
            The ``pass.json`` payload as a dict.
        """
        stamps_field: dict[str, object] = {
            "key": "stamps",
            "label": "Tampons",
            "value": f"{card.stamps} / {program.stamps_required}",
        }
        if program.default_change_message:
            stamps_field["changeMessage"] = program.default_change_message
        store_card: dict[str, object] = {"primaryFields": [stamps_field]}
        if program.reward_label:
            store_card["secondaryFields"] = [{"key": "reward", "label": "Récompense", "value": program.reward_label}]
        if card.current_offer:
            store_card["auxiliaryFields"] = [
                {"key": "offer", "label": "Offre", "value": card.current_offer, "changeMessage": "%@"}
            ]
        return {
            "formatVersion": 1,
            "passTypeIdentifier": signing_material.pass_type_identifier,
            "teamIdentifier": signing_material.team_id,
            "organizationName": program.organization_name,
            "description": program.description or f"Carte de fidélité {program.organization_name}",
            "serialNumber": card.serial_number,
            "backgroundColor": self._rgb_string(program.background_color, _DEFAULT_BACKGROUND),
            "foregroundColor": self._rgb_string(program.foreground_color, _DEFAULT_FOREGROUND),
            "labelColor": self._rgb_string(program.label_color, _DEFAULT_LABEL),
            "barcodes": [
                {"format": "PKBarcodeFormatQR", "message": card.serial_number, "messageEncoding": "iso-8859-1"}
            ],
            "webServiceURL": web_service_url,
            "authenticationToken": card.authentication_token,
            "storeCard": store_card,
        }

    def render_default_icons(self, program: LoyaltyProgram) -> dict[str, bytes]:
        """Render the mandatory icon set as brand-colored PNGs.

        Args:
            program: Program whose colors tint the icon.

        Returns:
            Icon bytes by filename (``icon.png`` / ``icon@2x.png`` / ``icon@3x.png``).
        """
        background = self._parse_color(program.background_color, _DEFAULT_BACKGROUND)
        foreground = self._parse_color(program.foreground_color, _DEFAULT_FOREGROUND)
        return {filename: self._render_icon(size, background, foreground) for filename, size in _ICON_SIZES.items()}

    def _render_logo_images(self, logo_url: str | None) -> dict[str, bytes]:
        """Fetch the merchant logo and render the Wallet logo set — best-effort.

        Args:
            logo_url: The program's logo URL, if any.

        Returns:
            ``logo.png`` / ``logo@2x.png`` / ``logo@3x.png`` bytes, or an empty dict when
            there is no logo or it cannot be fetched/decoded (the pass still ships its icons).
        """
        if not logo_url:
            return {}
        try:
            response = httpx.get(logo_url, timeout=_LOGO_FETCH_TIMEOUT_SECONDS, follow_redirects=True)
            response.raise_for_status()
            return self._logo_images_from_bytes(response.content)
        except Exception as error:
            logger.info("Wallet logo skipped for %r: %s", logo_url, error)
            return {}

    @staticmethod
    def _logo_images_from_bytes(raw: bytes) -> dict[str, bytes]:
        """Render logo.png/@2x/@3x from a source image, preserving aspect ratio and transparency."""
        source = Image.open(BytesIO(raw)).convert("RGBA")
        images: dict[str, bytes] = {}
        for filename, height in _LOGO_HEIGHTS.items():
            ratio = height / source.height
            width = min(round(source.width * ratio), _LOGO_MAX_WIDTHS[filename])
            resized = source.resize((max(width, 1), height), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            resized.save(buffer, format="PNG")
            images[filename] = buffer.getvalue()
        return images

    @staticmethod
    def _render_icon(size: int, background: tuple[int, int, int], foreground: tuple[int, int, int]) -> bytes:
        """Render a single square icon: brand background with a centered disc."""
        image = Image.new("RGB", (size, size), background)
        draw = ImageDraw.Draw(image)
        margin = max(2, size // 5)
        draw.ellipse((margin, margin, size - margin, size - margin), fill=foreground)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def _build_manifest(files: dict[str, bytes]) -> bytes:
        """Return ``manifest.json`` — the SHA-1 (Apple spec) of every bundled file."""
        manifest = {name: hashlib.sha1(content).hexdigest() for name, content in files.items()}
        return json.dumps(manifest, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    @staticmethod
    def _sign_manifest(manifest: bytes, signing_material: WalletSigningMaterial) -> bytes:
        """Return a detached PKCS#7 (DER) signature of the manifest, chained to WWDR."""
        certificate = load_pem_x509_certificate(signing_material.signing_certificate.encode("utf-8"))
        private_key = serialization.load_pem_private_key(
            signing_material.signing_private_key.encode("utf-8"), password=None
        )
        wwdr = load_pem_x509_certificate(signing_material.wwdr_certificate.encode("utf-8"))
        return (
            pkcs7.PKCS7SignatureBuilder()
            .set_data(manifest)
            .add_signer(certificate, private_key, hashes.SHA256())
            .add_certificate(wwdr)
            .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature, pkcs7.PKCS7Options.Binary])
        )

    @staticmethod
    def _zip(files: dict[str, bytes]) -> bytes:
        """Zip the named files into a single ``.pkpass`` archive."""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        return buffer.getvalue()

    @staticmethod
    def _to_bytes(payload: dict[str, object]) -> bytes:
        """Serialize a payload to the exact UTF-8 bytes that get hashed and bundled."""
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    @staticmethod
    def _web_service_url() -> str:
        """PassKit web-service base URL — the device appends ``/v1/...`` to it."""
        return f"{settings.api_base_url.rstrip('/')}/api/v1/wallet"

    def _rgb_string(self, value: str | None, fallback: tuple[int, int, int]) -> str:
        """Normalize a stored color to the ``rgb(r, g, b)`` form Apple expects."""
        red, green, blue = self._parse_color(value, fallback)
        return f"rgb({red}, {green}, {blue})"

    @staticmethod
    def _parse_color(value: str | None, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
        """Parse a ``#rrggbb`` or ``rgb(r,g,b)`` string, falling back when malformed."""
        if not value:
            return fallback
        text = value.strip()
        if text.startswith("#"):
            digits = text[1:]
            if len(digits) == 3:
                digits = "".join(character * 2 for character in digits)
            if len(digits) == 6:
                try:
                    return (int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16))
                except ValueError:
                    return fallback
            return fallback
        if text.lower().startswith("rgb") and "(" in text and ")" in text:
            inside = text[text.find("(") + 1 : text.find(")")]
            parts = [part.strip() for part in inside.split(",")]
            if len(parts) == 3 and all(part.isdigit() for part in parts):
                return (min(255, int(parts[0])), min(255, int(parts[1])), min(255, int(parts[2])))
        return fallback


wallet_pass_service = WalletPassService()
