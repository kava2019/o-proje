from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..models import CommandIn, DeviceOut, RenameIn
from ..state import DeviceRegistry, get_registry

router = APIRouter(
    prefix="/api/devices",
    tags=["devices"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[DeviceOut])
async def list_devices(registry: DeviceRegistry = Depends(get_registry)):
    return registry.snapshot()


@router.post("/{device_id}/command", status_code=202)
async def send_command(
    device_id: str,
    body: CommandIn,
    registry: DeviceRegistry = Depends(get_registry),
):
    if not registry.exists(device_id):
        raise HTTPException(status_code=404, detail="cihaz bulunamadı")
    sent = await registry.send_command(device_id, body.state)
    if not sent:
        raise HTTPException(status_code=503, detail="gateway bağlı değil")
    return {"accepted": True}


@router.put("/{device_id}/name", response_model=DeviceOut)
async def rename_device(
    device_id: str,
    body: RenameIn,
    registry: DeviceRegistry = Depends(get_registry),
):
    updated = registry.rename(device_id, body.name)
    if updated is None:
        raise HTTPException(status_code=404, detail="cihaz bulunamadı")
    await registry.broadcast({"type": "device_update", "device": updated.model_dump()})
    return updated
