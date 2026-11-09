"""Bodies of the PassKit web service, the protocol Apple's devices speak (its field names are Apple's)."""

from pydantic import BaseModel


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
