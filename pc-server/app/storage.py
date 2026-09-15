"""Sadece cihaz isimlerinin diske (JSON) yazılması. Başka hiçbir şey kalıcı değil."""
import json
from pathlib import Path


def load_names(path: str) -> dict[str, str]:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_names(path: str, names: dict[str, str]) -> None:
    p = Path(path)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(names, f, ensure_ascii=False, indent=2, sort_keys=True)
    tmp.replace(p)
