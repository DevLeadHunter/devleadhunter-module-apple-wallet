"""Merchant auth service — provision, authenticate and resolve a merchant login.

A merchant manages their own loyalty program through a dedicated account, separate from
the operator's ``User`` (the handover model, like the Storyblok space for websites). The
JWT it issues carries ``type: merchant`` so operator and merchant tokens never cross over.
"""

from __future__ import annotations

import re
import secrets
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from models.merchant_account import MerchantAccount
from services.auth_service import AuthService

_MERCHANT_TOKEN_TYPE = "merchant"
_MERCHANT_EMAIL_DOMAIN = "merchant.dibodev.fr"

merchant_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/merchant/login", auto_error=True)


class MerchantAuthService:
    """Provisioning, authentication and token resolution for merchant logins."""

    def provision(self, db: Session, program_id: int, *, organization_name: str) -> tuple[MerchantAccount, str]:
        """Create or reset the merchant login for a program, returning the fresh password.

        Args:
            db: Database session.
            program_id: Program the account manages.
            organization_name: Merchant name, used to build a readable email.

        Returns:
            The account and its new plaintext password (shown once, for handover).
        """
        account = db.query(MerchantAccount).filter(MerchantAccount.program_id == program_id).first()
        password = secrets.token_urlsafe(9)
        if account is None:
            account = MerchantAccount(
                program_id=program_id,
                email=self._build_email(organization_name),
                hashed_password=AuthService.hash_password(password),
            )
            db.add(account)
        else:
            account.hashed_password = AuthService.hash_password(password)
            account.is_active = True
        db.commit()
        db.refresh(account)
        return account, password

    def authenticate(self, db: Session, email: str, password: str) -> MerchantAccount | None:
        """Return the merchant when the credentials match an active account, else ``None``.

        Args:
            db: Database session.
            email: Submitted email.
            password: Submitted password.

        Returns:
            The authenticated account, or ``None`` (the failure causes are indistinguishable).
        """
        account = db.query(MerchantAccount).filter(MerchantAccount.email == email).first()
        if account is None or not account.is_active:
            return None
        if not AuthService.verify_password(password, account.hashed_password):
            return None
        account.last_login_at = datetime.now(UTC).replace(tzinfo=None)
        db.commit()
        return account

    def create_token(self, account: MerchantAccount) -> str:
        """Issue a merchant-typed JWT for an account.

        Args:
            account: The merchant to encode.

        Returns:
            The signed token.
        """
        return AuthService.create_access_token(
            {
                "sub": account.email,
                "type": _MERCHANT_TOKEN_TYPE,
                "merchant_id": account.id,
                "program_id": account.program_id,
            }
        )

    @staticmethod
    def _build_email(organization_name: str) -> str:
        """Build a readable, unique login email from the merchant name."""
        slug = re.sub(r"[^a-z0-9]+", "-", organization_name.lower()).strip("-")[:32] or "merchant"
        return f"{slug}-{secrets.token_hex(3)}@{_MERCHANT_EMAIL_DOMAIN}"


merchant_auth_service = MerchantAuthService()


def get_current_merchant(
    token: str = Depends(merchant_oauth2_scheme), db: Session = Depends(get_db)
) -> MerchantAccount:
    """Resolve the merchant a JWT belongs to, rejecting non-merchant or invalid tokens.

    Args:
        token: Raw bearer JWT.
        db: Database session.

    Returns:
        The authenticated merchant account.

    Raises:
        HTTPException: 401 when the token is invalid, not a merchant token, or dangling.
    """
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate merchant credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as error:
        raise exception from error
    if payload.get("type") != _MERCHANT_TOKEN_TYPE:
        raise exception
    merchant_id = payload.get("merchant_id")
    account = db.query(MerchantAccount).filter(MerchantAccount.id == merchant_id).first() if merchant_id else None
    if account is None or not account.is_active:
        raise exception
    return account
