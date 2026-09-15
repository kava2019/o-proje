"""Donanımsız test: pi-gateway yerine pc-server'ın /ws/gateway ucuna doğrudan
bağlanıp sahte bir ESP'nin tetiklediği HELLO/STATUS trafiğini simüle eder.

Gerçek nRF24 paket formatını değil, gateway'in PC'ye gönderdiği JSON mesaj
formatını (announce/status) taklit eder - yani "gateway"nin kendisi gibi
davranır. Böylece radyo, Pi ve ESP olmadan tarayıcı arayüzünde cihaz
belirmesi / isim verme / aç-kapat akışı uçtan uca denenebilir.

Bağımlılık: websockets (pc-server veya pi-gateway'in venv'inde zaten kurulu).

Kullanım:
    python tools/fake_esp.py --device-id aabbccddeeff --type LIGHT

PC'den gelen "command" mesajına --ack-delay kadar sonra otomatik "status"
ile cevap verir; gerçek bir ESP'nin nRF24 üzerinden CMD alıp STATUS
döndürmesini taklit eder.

NOT: pc-server aynı anda tek bir gateway bağlantısı kabul eder (yenisi
gelince eskisini kapatır) - gerçek pi-gateway çalışıyorsa önce onu durdur.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

import websockets


async def run(args: argparse.Namespace) -> None:
    device_id = args.device_id.lower()
    if len(device_id) != 12:
        sys.exit("--device-id tam 12 hex karakter (6 byte) olmalı, ör. aabbccddeeff")

    state = "off"
    url = f"ws://{args.host}:{args.port}/ws/gateway"

    async with websockets.connect(url) as ws:
        print(f"[bağlandı] {url} (sahte gateway olarak)")

        await ws.send(json.dumps({"type": "radio_status", "radio_ok": True}))
        await ws.send(
            json.dumps({"type": "announce", "device_id": device_id, "device_type": args.type})
        )
        print(f"[gönderildi] announce device_id={device_id} device_type={args.type}")

        async for raw in ws:
            msg = json.loads(raw)
            print(f"[PC'den geldi] {msg}")
            if msg.get("type") == "command" and msg.get("device_id") == device_id:
                state = msg["state"]
                await asyncio.sleep(args.ack_delay)
                await ws.send(
                    json.dumps(
                        {
                            "type": "status",
                            "device_id": device_id,
                            "device_type": args.type,
                            "state": state,
                        }
                    )
                )
                print(f"[gönderildi] status state={state}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--device-id", required=True, help="12 hex karakter, ör. aabbccddeeff")
    parser.add_argument("--type", choices=["PLUG", "LIGHT"], default="LIGHT")
    parser.add_argument(
        "--ack-delay", type=float, default=0.2,
        help="CMD sonrası STATUS'u kaç saniye gecikmeli göndersin (varsayılan 0.2)",
    )
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
