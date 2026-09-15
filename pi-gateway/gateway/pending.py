"""Komut teslim garantisi - retry/timeout mantığı TEK yerde burada durur.

Her CMD paketine artan bir seq numarası konur. ESP komutu uygulayınca aynı
seq ile STATUS döner (bkz. protocol.py). cmd_timeout_ms içinde cevap
gelmezse, cmd_retries kadar daha (aynı seq ile) tekrar denenir. Hepsi
tükenirse cihaz "yanıtsız" sayılır ve PC'ye bildirilir.

Zaman aşımı süresi ve deneme sayısı burada sabit kodlanmıyor:
config.json -> GatewayConfig.cmd_timeout_ms / cmd_retries üzerinden gelir.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, Dict

from .config import GatewayConfig
from .protocol import MSG_CMD, RadioPacket
from .radio import NRF24Radio

logger = logging.getLogger(__name__)

UnresponsiveCallback = Callable[[bytes], Awaitable[None]]


class PendingCommands:
    def __init__(
        self,
        config: GatewayConfig,
        radio: NRF24Radio,
        on_unresponsive: UnresponsiveCallback,
    ) -> None:
        self._config = config
        self._radio = radio
        self._on_unresponsive = on_unresponsive
        self._seq = 0
        self._waiting: Dict[int, asyncio.Event] = {}

    def _next_seq(self) -> int:
        self._seq = (self._seq + 1) & 0xFFFF
        return self._seq

    def resolve(self, seq: int) -> bool:
        """Radyo poll döngüsü bir STATUS paketi aldığında çağırır.

        seq bilinen bir bekleyen komuta aitse ilgili event'i tetikler ve
        True döner; değilse (ör. gecikmiş/tekrar gelen bir cevapsa) True
        dönmez, çağıran yine de STATUS'u PC'ye iletmeye devam eder.
        """
        event = self._waiting.get(seq)
        if event is None:
            return False
        event.set()
        return True

    async def send_command(self, device_id: bytes, device_type: int, state: int) -> None:
        seq = self._next_seq()
        event = asyncio.Event()
        self._waiting[seq] = event

        packet = RadioPacket(
            msg_type=MSG_CMD,
            network_id=self._config.network_id,
            device_id=device_id,
            device_type=device_type,
            seq=seq,
            state=state,
        )
        timeout_s = self._config.cmd_timeout_ms / 1000
        attempts = self._config.cmd_retries + 1

        try:
            for attempt in range(1, attempts + 1):
                self._radio.send(packet.pack())
                try:
                    await asyncio.wait_for(event.wait(), timeout=timeout_s)
                    return  # ack geldi
                except asyncio.TimeoutError:
                    logger.warning(
                        "cihaz %s cevap vermedi (deneme %d/%d, seq=%d)",
                        device_id.hex(), attempt, attempts, seq,
                    )
            await self._on_unresponsive(device_id)
        finally:
            self._waiting.pop(seq, None)
