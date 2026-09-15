from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import TypeAdapter, ValidationError

from ..models import (
    GatewayAnnounceMsg,
    GatewayInbound,
    GatewayRadioStatusMsg,
    GatewayStatusMsg,
    GatewayUnresponsiveMsg,
)
from ..state import DeviceRegistry, get_registry_ws

router = APIRouter()

_inbound_adapter = TypeAdapter(GatewayInbound)


async def _handle_message(registry: DeviceRegistry, raw: dict) -> None:
    try:
        msg = _inbound_adapter.validate_python(raw)
    except ValidationError:
        return

    if isinstance(msg, (GatewayStatusMsg, GatewayAnnounceMsg)):
        state = msg.state if isinstance(msg, GatewayStatusMsg) else None
        device = registry.register_or_update(msg.device_id, msg.device_type, state)
        await registry.broadcast({"type": "device_update", "device": device.model_dump()})

    elif isinstance(msg, GatewayUnresponsiveMsg):
        device = registry.mark_unresponsive(msg.device_id)
        if device is not None:
            await registry.broadcast({"type": "device_update", "device": device.model_dump()})

    elif isinstance(msg, GatewayRadioStatusMsg):
        registry.set_radio_ok(msg.radio_ok)
        await registry.broadcast(registry.gateway_status_message())


@router.websocket("/ws/gateway")
async def gateway_ws(
    websocket: WebSocket, registry: DeviceRegistry = Depends(get_registry_ws)
):
    await websocket.accept()
    await registry.set_gateway_ws(websocket)
    await registry.broadcast(registry.gateway_status_message())
    try:
        while True:
            raw = await websocket.receive_json()
            await _handle_message(registry, raw)
    except WebSocketDisconnect:
        pass
    finally:
        if registry.clear_gateway_ws(websocket):
            await registry.broadcast(registry.snapshot_message())
