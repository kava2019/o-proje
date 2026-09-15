"""config.json yükleyici.

config.json diske gerçek PC IP'siyle yazılır ve .gitignore'da tutulur;
config.example.json şablon olarak repo'da kalır (bkz. pi-gateway/SETUP.md).

cmd_timeout_ms / cmd_retries buradan geliyor, pending.py'de sabit
kodlanmıyor - sahada ayar gerekirse sadece config.json değişir.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Union

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config.json"
_REQUIRED_FIELDS = ("pc_host", "pc_port", "network_id", "rf_channel")


@dataclass(frozen=True)
class GatewayConfig:
    pc_host: str
    pc_port: int
    network_id: int
    rf_channel: int
    cmd_timeout_ms: int = 500
    cmd_retries: int = 2

    @property
    def pc_ws_url(self) -> str:
        return f"ws://{self.pc_host}:{self.pc_port}/ws/gateway"


def load_config(path: Union[Path, str] = _DEFAULT_PATH) -> GatewayConfig:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"{p} yok. config.example.json'u kopyalayıp PC IP'sini yaz: "
            f"cp config.example.json config.json"
        )
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)

    missing = [k for k in _REQUIRED_FIELDS if k not in data]
    if missing:
        raise ValueError(f"config.json eksik alanlar: {missing}")

    return GatewayConfig(
        pc_host=data["pc_host"],
        pc_port=int(data["pc_port"]),
        network_id=int(data["network_id"]),
        rf_channel=int(data["rf_channel"]),
        cmd_timeout_ms=int(data.get("cmd_timeout_ms", 500)),
        cmd_retries=int(data.get("cmd_retries", 2)),
    )
