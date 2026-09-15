"""Bellekteki cihaz durumu ve WS yayın (broadcast) mantığı.

Kalıcı olan tek şey isimler (storage.py üzerinden devices.json). device_type,
state, online hep bellekte tutulur; süreç yeniden başladığında sıfırlanır ve
cihazlar HELLO/announce/status ile kendilerini bildirdikçe yeniden dolar.

Bilinen (adı diskte kayıtlı) ama henüz hiç haber alınmamış bir cihaz, PC
yeniden başladığında listede "çevrimdışı" ve tipi bilinmez olarak görünür;
gateway (yeniden) bağlanıp WHOIS yayınladığında cihazlar HELLO ile cevap
verince bilgiler tazelenir.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Request, WebSocket

from . import storage
from .models import DeviceOut


@dataclass
class _Device:
    device_id: str
    name: str
    device_type: Optional[str] = None
    state: Optional[str] = None
    online: bool = False

    def to_out(self) -> DeviceOut:
        return DeviceOut(
            device_id=self.device_id,
            name=self.name,
            device_type=self.device_type,
            state=self.state,
            online=self.online,
        )


class DeviceRegistry:
    def __init__(self, devices_file: str) -> None:
        self._devices_file = devices_file
        self._devices: dict[str, _Device] = {}
        self._ui_clients: set[WebSocket] = set()
        self._gateway_ws: Optional[WebSocket] = None
        self.gateway_connected: bool = False
        self.radio_ok: Optional[bool] = None

        for device_id, name in storage.load_names(devices_file).items():
            self._devices[device_id] = _Device(device_id=device_id, name=name)

    # --- isimler (kalıcı) ---

    def _persist_names(self) -> None:
        names = {d.device_id: d.name for d in self._devices.values()}
        storage.save_names(self._devices_file, names)

    @staticmethod
    def _default_name(device_id: str) -> str:
        return f"Cihaz-{device_id[-6:]}"

    def rename(self, device_id: str, name: str) -> Optional[DeviceOut]:
        dev = self._devices.get(device_id)
        if dev is None:
            return None
        dev.name = name
        self._persist_names()
        return dev.to_out()

    # --- sorgular ---

    def exists(self, device_id: str) -> bool:
        return device_id in self._devices

    def get(self, device_id: str) -> Optional[DeviceOut]:
        dev = self._devices.get(device_id)
        return dev.to_out() if dev else None

    def snapshot(self) -> list[DeviceOut]:
        return [d.to_out() for d in self._devices.values()]

    # --- gateway'den gelen olaylar (isim ASLA ezilmez) ---

    def register_or_update(
        self, device_id: str, device_type: str, state: Optional[str] = None
    ) -> DeviceOut:
        dev = self._devices.get(device_id)
        if dev is None:
            dev = _Device(
                device_id=device_id,
                name=self._default_name(device_id),
                device_type=device_type,
                online=True,
            )
            self._devices[device_id] = dev
            self._persist_names()
        else:
            dev.device_type = device_type
            dev.online = True
        if state is not None:
            dev.state = state
        return dev.to_out()

    def mark_unresponsive(self, device_id: str) -> Optional[DeviceOut]:
        dev = self._devices.get(device_id)
        if dev is None:
            return None
        dev.online = False
        return dev.to_out()

    def set_gateway_connected(self, connected: bool) -> None:
        self.gateway_connected = connected
        if not connected:
            self.radio_ok = None
            for dev in self._devices.values():
                dev.online = False

    def set_radio_ok(self, radio_ok: bool) -> None:
        self.radio_ok = radio_ok

    # --- tarayıcı WS istemcileri ---

    def add_ui_client(self, ws: WebSocket) -> None:
        self._ui_clients.add(ws)

    def remove_ui_client(self, ws: WebSocket) -> None:
        self._ui_clients.discard(ws)

    async def broadcast(self, message: dict) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._ui_clients):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._ui_clients.discard(ws)

    def gateway_status_message(self) -> dict:
        return {
            "type": "gateway_status",
            "connected": self.gateway_connected,
            "radio_ok": self.radio_ok,
        }

    def snapshot_message(self) -> dict:
        return {
            "type": "snapshot",
            "devices": [d.model_dump() for d in self.snapshot()],
            "gateway_connected": self.gateway_connected,
            "radio_ok": self.radio_ok,
        }

    # --- gateway WS bağlantısı (tek gateway varsayılır) ---

    async def set_gateway_ws(self, ws: WebSocket) -> None:
        old = self._gateway_ws
        self._gateway_ws = ws
        self.set_gateway_connected(True)
        if old is not None and old is not ws:
            try:
                await old.close()
            except Exception:
                pass

    def clear_gateway_ws(self, ws: WebSocket) -> bool:
        """ws hâlâ güncel bağlantıysa temizler. Eski/artık bağlantının
        disconnect handler'ı, araya giren yeni bağlantıyı yanlışlıkla
        temizlemesin diye eşleşme kontrolü yapılır."""
        if self._gateway_ws is ws:
            self._gateway_ws = None
            self.set_gateway_connected(False)
            return True
        return False

    async def send_command(self, device_id: str, state: str) -> bool:
        if self._gateway_ws is None:
            return False
        await self._gateway_ws.send_json(
            {"type": "command", "device_id": device_id, "state": state}
        )
        return True


def get_registry(request: Request) -> DeviceRegistry:
    return request.app.state.registry


def get_registry_ws(websocket: WebSocket) -> DeviceRegistry:
    return websocket.app.state.registry
