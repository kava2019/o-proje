"""pi-gateway giriş noktası.

Açılışta PC'ye WebSocket ile BAĞLANIR (Pi sunucu değil, istemci).
Bağlantı koparsa ws_client.py 5 saniyede bir yeniden dener.
PC'den gelen komutu nRF24 üzerinden ilgili ESP'ye yollar (pending.py
teslim garantisini uygular). ESP'den gelen durum mesajını PC'ye iletir.

Radyo başlatılamazsa (radio.ok=False) çökmez; PC'ye bağlı kalır ve
"radio_status" ile bunu bildirir.
"""
from __future__ import annotations

import asyncio
import logging

from .config import load_config
from .pending import PendingCommands
from .protocol import (
    MSG_HELLO,
    MSG_STATUS,
    MSG_HELLO_ACK,
    MSG_WHOIS,
    RadioPacket,
    device_type_from_str,
    device_type_to_str,
    state_from_str,
    state_to_str,
)
from .radio import NRF24Radio
from .ws_client import PCConnection

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

RADIO_POLL_INTERVAL_S = 0.02


class Gateway:
    def __init__(self) -> None:
        self.config = load_config()
        self.radio = NRF24Radio(self.config.rf_channel)
        self.pc = PCConnection(self.config.pc_ws_url)
        self.pending = PendingCommands(self.config, self.radio, self._on_unresponsive)
        # ESP'lerden HELLO/STATUS ile öğrenilen device_type önbelleği - PC'nin
        # "command" mesajı device_type taşımaz, CMD paketi kurarken buradan
        # okunur.
        self._known_types: dict[bytes, int] = {}

    async def _on_unresponsive(self, device_id: bytes) -> None:
        await self.pc.send({"type": "unresponsive", "device_id": device_id.hex()})

    async def _on_pc_connect(self) -> None:
        await self.pc.send({"type": "radio_status", "radio_ok": self.radio.ok})
        whois = RadioPacket(
            msg_type=MSG_WHOIS,
            network_id=self.config.network_id,
            device_id=b"\x00" * 6,
            device_type=0,
            seq=0,
            state=0,
        )
        self.radio.send(whois.pack())
        logger.info("WHOIS yayınlandı (radio_ok=%s)", self.radio.ok)

    async def _on_pc_message(self, msg: dict) -> None:
        if msg.get("type") != "command":
            return
        device_id = bytes.fromhex(msg["device_id"])
        device_type = self._known_types.get(device_id)
        if device_type is None:
            logger.warning(
                "cihaz %s için device_type bilinmiyor (henüz HELLO/STATUS gelmedi), PLUG varsayılıyor",
                msg["device_id"],
            )
            device_type = device_type_from_str("PLUG")
        state = state_from_str(msg["state"])
        await self.pending.send_command(device_id, device_type, state)

    async def _handle_radio_packet(self, raw: bytes) -> None:
        pkt = RadioPacket.unpack(raw)
        if pkt.network_id != self.config.network_id:
            return  # başka bir kurulumun paketi, yok say

        if pkt.msg_type == MSG_STATUS:
            self._known_types[pkt.device_id] = pkt.device_type
            self.pending.resolve(pkt.seq)
            await self.pc.send(
                {
                    "type": "status",
                    "device_id": pkt.device_id.hex(),
                    "device_type": device_type_to_str(pkt.device_type),
                    "state": state_to_str(pkt.state),
                }
            )

        elif pkt.msg_type == MSG_HELLO:
            self._known_types[pkt.device_id] = pkt.device_type
            ack = RadioPacket(
                msg_type=MSG_HELLO_ACK,
                network_id=self.config.network_id,
                device_id=pkt.device_id,
                device_type=pkt.device_type,
                seq=pkt.seq,
                state=0,
            )
            self.radio.send(ack.pack())
            await self.pc.send(
                {
                    "type": "announce",
                    "device_id": pkt.device_id.hex(),
                    "device_type": device_type_to_str(pkt.device_type),
                }
            )

    async def _radio_poll_loop(self) -> None:
        while True:
            raw = self.radio.poll()
            if raw is not None:
                try:
                    await self._handle_radio_packet(raw)
                except Exception:
                    logger.exception("radyo paketi işlenirken hata")
            await asyncio.sleep(RADIO_POLL_INTERVAL_S)

    async def run(self) -> None:
        await asyncio.gather(
            self.pc.run(self._on_pc_connect, self._on_pc_message),
            self._radio_poll_loop(),
        )


def main() -> None:
    gateway = Gateway()
    asyncio.run(gateway.run())


if __name__ == "__main__":
    main()
