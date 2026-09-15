from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from ..state import DeviceRegistry, get_registry_ws

router = APIRouter()


@router.websocket("/ws/ui")
async def ui_ws(websocket: WebSocket, registry: DeviceRegistry = Depends(get_registry_ws)):
    await websocket.accept()
    registry.add_ui_client(websocket)
    await websocket.send_json(registry.snapshot_message())
    try:
        while True:
            # Tarayıcı bu kanaldan komut göndermez (komutlar REST üzerinden
            # gider); burada sadece disconnect'i algılamak için bekliyoruz.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        registry.remove_ui_client(websocket)
