"""nRF24 radyo paketi (de)serileştirme.

Bu dosyadaki byte dizilimi esp32-node/protocol.h ile birebir aynı olmak
zorunda. Format: little-endian, 1+1+6+1+2+1 = 12 byte, padding yok.

    msg_type    uint8   MSG_* sabitlerinden biri
    network_id  uint8   kurulum kimliği (config'den)
    device_id   6 byte  ESP32 MAC adresi (ham byte, endianness yok)
    device_type uint8   DEVICE_* sabitlerinden biri
    seq         uint16  CMD/STATUS eşleştirme sıra numarası
    state       uint8   STATE_* sabitlerinden biri
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

# --- msg_type ---
MSG_CMD = 0x01
MSG_STATUS = 0x02
MSG_HELLO = 0x03
MSG_WHOIS = 0x04
MSG_HELLO_ACK = 0x05

# --- device_type ---
DEVICE_PLUG = 0x00
DEVICE_LIGHT = 0x01

# --- state ---
STATE_OFF = 0x00
STATE_ON = 0x01

# little-endian, padding yok: B(msg_type) B(network_id) 6s(device_id)
# B(device_type) H(seq) B(state)
_STRUCT = struct.Struct("<BB6sBHB")
PACKET_SIZE = _STRUCT.size
assert PACKET_SIZE == 12, f"beklenmeyen paket boyutu: {PACKET_SIZE}"


@dataclass(frozen=True)
class RadioPacket:
    msg_type: int
    network_id: int
    device_id: bytes  # tam 6 byte, ESP32 MAC'i
    device_type: int
    seq: int
    state: int

    def __post_init__(self) -> None:
        if len(self.device_id) != 6:
            raise ValueError("device_id tam 6 byte olmalı")

    def pack(self) -> bytes:
        return _STRUCT.pack(
            self.msg_type,
            self.network_id,
            self.device_id,
            self.device_type,
            self.seq,
            self.state,
        )

    @classmethod
    def unpack(cls, raw: bytes) -> "RadioPacket":
        if len(raw) != PACKET_SIZE:
            raise ValueError(f"paket {PACKET_SIZE} byte olmalı, {len(raw)} byte geldi")
        msg_type, network_id, device_id, device_type, seq, state = _STRUCT.unpack(raw)
        return cls(msg_type, network_id, device_id, device_type, seq, state)


def device_id_to_hex(device_id: bytes) -> str:
    """PC/gateway tarafında JSON'a yazılan ve WS mesajlarında taşınan biçim."""
    return device_id.hex()


def device_id_from_hex(text: str) -> bytes:
    raw = bytes.fromhex(text)
    if len(raw) != 6:
        raise ValueError("device_id hex string 12 karakter (6 byte) olmalı")
    return raw


# pc-server tarafı device_type/state'i "PLUG"/"LIGHT" ve "on"/"off" string'leriyle
# konuşuyor (bkz. pc-server/app/models.py); radyo paketindeki numerik
# sabitlerle bu string'ler arasındaki çeviri burada, tek yerde yapılır.


def device_type_to_str(value: int) -> str:
    return "LIGHT" if value == DEVICE_LIGHT else "PLUG"


def device_type_from_str(value: str) -> int:
    return DEVICE_LIGHT if value == "LIGHT" else DEVICE_PLUG


def state_to_str(value: int) -> str:
    return "on" if value == STATE_ON else "off"


def state_from_str(value: str) -> int:
    return STATE_ON if value == "on" else STATE_OFF


def _pack_manual(p: RadioPacket) -> bytes:
    """struct modülünü kullanmadan, elle byte dizen bağımsız referans.

    Amaç: _STRUCT format string'inde bir yazım hatası olsa bile (ör. yanlış
    endianness ya da yanlış tip harfi) bunu struct'ın kendi çıktısına değil,
    bağımsız bir hesaba karşı test etmek.
    """
    seq_lo = p.seq & 0xFF
    seq_hi = (p.seq >> 8) & 0xFF
    return (
        bytes([p.msg_type, p.network_id])
        + p.device_id
        + bytes([p.device_type, seq_lo, seq_hi, p.state])
    )


# esp32-node/protocol.h içindeki radioPacketSelfTest() ile aynı örnek değerler.
SELFTEST_PACKET = RadioPacket(
    msg_type=MSG_CMD,
    network_id=0x2A,
    device_id=bytes.fromhex("aabbccddeeff"),
    device_type=DEVICE_LIGHT,
    seq=0x0102,
    state=STATE_ON,
)


def run_selftest() -> str:
    packed = SELFTEST_PACKET.pack()
    manual = _pack_manual(SELFTEST_PACKET)
    assert packed == manual, (
        f"struct.pack çıktısı elle hesaplanan byte dizisiyle uyuşmuyor: "
        f"{packed.hex()} != {manual.hex()}"
    )
    assert len(packed) == PACKET_SIZE
    assert RadioPacket.unpack(packed) == SELFTEST_PACKET
    return packed.hex()


if __name__ == "__main__":
    hex_out = run_selftest()
    print("protocol.py selftest OK")
    print(f"ornek paket ({PACKET_SIZE} byte): {hex_out}")
