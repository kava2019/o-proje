from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

DeviceType = Literal["PLUG", "LIGHT"]
DeviceState = Literal["on", "off"]


class DeviceOut(BaseModel):
    device_id: str
    name: str
    device_type: DeviceType | None = None
    state: DeviceState | None = None
    online: bool


class CommandIn(BaseModel):
    state: DeviceState


class RenameIn(BaseModel):
    name: str


# --- pi-gateway -> pc-server WS mesajları (/ws/gateway) ---


class GatewayStatusMsg(BaseModel):
    type: Literal["status"]
    device_id: str
    device_type: DeviceType
    state: DeviceState


class GatewayAnnounceMsg(BaseModel):
    type: Literal["announce"]
    device_id: str
    device_type: DeviceType


class GatewayUnresponsiveMsg(BaseModel):
    type: Literal["unresponsive"]
    device_id: str


class GatewayRadioStatusMsg(BaseModel):
    type: Literal["radio_status"]
    radio_ok: bool


GatewayInbound = Annotated[
    Union[
        GatewayStatusMsg,
        GatewayAnnounceMsg,
        GatewayUnresponsiveMsg,
        GatewayRadioStatusMsg,
    ],
    Field(discriminator="type"),
]
