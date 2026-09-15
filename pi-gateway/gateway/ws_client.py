"""PC'ye WebSocket istemcisi.

Pi sunucu DEĞİL, istemci: açılışta PC'ye bağlanır. Bağlantı koparsa ya da
hiç kurulamazsa 5 saniyede bir yeniden dener.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Awaitable, Callable, Optional

import websockets

logger = logging.getLogger(__name__)

RECONNECT_DELAY_S = 5

OnConnect = Callable[[], Awaitable[None]]
OnMessage = Callable[[dict], Awaitable[None]]


class PCConnection:
    def __init__(self, url: str) -> None:
        self._url = url
        self._ws: Optional["websockets.WebSocketClientProtocol"] = None

    @property
    def connected(self) -> bool:
        return self._ws is not None

    async def send(self, message: dict) -> None:
        if self._ws is None:
            return
        try:
            await self._ws.send(json.dumps(message))
        except Exception:
            logger.warning("PC'ye mesaj gönderilemedi (bağlantı kopmuş olabilir)")

    async def run(self, on_connect: OnConnect, on_message: OnMessage) -> None:
        while True:
            try:
                async with websockets.connect(self._url) as ws:
                    self._ws = ws
                    logger.info("PC'ye bağlanıldı: %s", self._url)
                    await on_connect()
                    async for raw in ws:
                        await on_message(json.loads(raw))
            except (OSError, websockets.WebSocketException) as exc:
                logger.warning("PC bağlantısı kurulamadı/koptu: %s", exc)
            except Exception:
                logger.exception("PC bağlantı döngüsünde beklenmeyen hata")
            finally:
                self._ws = None
            await asyncio.sleep(RECONNECT_DELAY_S)
