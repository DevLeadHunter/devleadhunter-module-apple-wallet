"""PassKit web service — the endpoints Apple's device calls for a wallet pass.

Mounted at ``/api/v1/wallet``, so the device appends ``/v1/...`` to the pass's
``webServiceURL`` (baked in by ``wallet_pass_service``). No app JWT here: requests are
authenticated by the pass's ``authenticationToken`` (``Authorization: ApplePass ...``).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from enums.wallet_registration_outcome import WalletRegistrationOutcome
from services.wallet_pass_service import wallet_pass_service
from services.wallet_passkit_service import wallet_passkit_service

router = APIRouter(prefix="/wallet", tags=["wallet"])
logger = logging.getLogger(__name__)

_PKPASS_MEDIA_TYPE = "application/vnd.apple.pkpass"
_REGISTRATION_STATUS: dict[str, int] = {
    WalletRegistrationOutcome.CREATED.value: status.HTTP_201_CREATED,
    WalletRegistrationOutcome.ALREADY_REGISTERED.value: status.HTTP_200_OK,
    WalletRegistrationOutcome.DELETED.value: status.HTTP_200_OK,
    WalletRegistrationOutcome.UNAUTHORIZED.value: status.HTTP_401_UNAUTHORIZED,
}


class DeviceRegistrationBody(BaseModel):
    """Body of a device registration request."""

    pushToken: str


class DeviceLogBody(BaseModel):
    """Body of a device log request."""

    logs: list[str] = []


class DeviceUpdatesResponse(BaseModel):
    """Response body listing the serials Apple should refresh."""

    lastUpdated: str
    serialNumbers: list[str]


@router.post("/v1/devices/{device_library_identifier}/registrations/{pass_type_identifier}/{serial_number}")
async def register_device(
    device_library_identifier: str,
    pass_type_identifier: str,
    serial_number: str,
    body: DeviceRegistrationBody,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Register a device's push token for a pass."""
    outcome = wallet_passkit_service.register_device(
        db,
        device_library_identifier=device_library_identifier,
        pass_type_identifier=pass_type_identifier,
        serial_number=serial_number,
        push_token=body.pushToken,
        pass_token=wallet_passkit_service.parse_pass_token(authorization),
    )
    return Response(status_code=_REGISTRATION_STATUS[outcome.value])


@router.delete("/v1/devices/{device_library_identifier}/registrations/{pass_type_identifier}/{serial_number}")
async def unregister_device(
    device_library_identifier: str,
    pass_type_identifier: str,
    serial_number: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Unregister a device from a pass."""
    outcome = wallet_passkit_service.unregister_device(
        db,
        device_library_identifier=device_library_identifier,
        serial_number=serial_number,
        pass_token=wallet_passkit_service.parse_pass_token(authorization),
    )
    return Response(status_code=_REGISTRATION_STATUS[outcome.value])


@router.get("/v1/devices/{device_library_identifier}/registrations/{pass_type_identifier}")
async def list_updated_serials(
    device_library_identifier: str,
    pass_type_identifier: str,
    passes_updated_since: str | None = Query(default=None, alias="passesUpdatedSince"),
    db: Session = Depends(get_db),
) -> Response:
    """Return the serials of the device's passes that changed since the given tag."""
    serials, last_updated = wallet_passkit_service.serials_updated_since(
        db,
        device_library_identifier=device_library_identifier,
        pass_type_identifier=pass_type_identifier,
        updated_since=passes_updated_since,
    )
    if not serials:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return Response(
        content=DeviceUpdatesResponse(lastUpdated=last_updated or "", serialNumbers=serials).model_dump_json(),
        media_type="application/json",
    )


@router.get("/v1/passes/{pass_type_identifier}/{serial_number}")
async def get_latest_pass(
    pass_type_identifier: str,
    serial_number: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Return the up-to-date ``.pkpass`` for a serial, authenticated by its pass token."""
    card = wallet_passkit_service.authenticated_card(
        db,
        serial_number=serial_number,
        pass_token=wallet_passkit_service.parse_pass_token(authorization),
    )
    if card is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    pkpass = wallet_pass_service.generate_for_card(db, card.user_id, card.id)
    return Response(content=pkpass, media_type=_PKPASS_MEDIA_TYPE)


@router.post("/v1/log")
async def collect_device_logs(body: DeviceLogBody) -> Response:
    """Accept PassKit device debug logs (useful while bringing the service up)."""
    for entry in body.logs:
        logger.info("PassKit device log: %s", entry)
    return Response(status_code=status.HTTP_200_OK)
