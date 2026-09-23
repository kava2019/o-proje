"""nRF24L01 sürücüsü - tek dosya, tek sınıf.

Donanım henüz kablolanmadığında ya da nRF24 modülü fiziksel olarak takılı
olmadığında bile gateway ÇÖKMEMELİ: bu durumda `ok=False` kalır, main.py
PC'ye "radyo yok" bilgisini iletir ve gateway PC'ye bağlı kalmaya devam
eder. Radyo takılınca değişmesi gereken tek dosya budur.

Kütüphane seçimi: circuitpython-nrf24l01 (Adafruit Blinka üzerinden).
Raspberry Pi için resmi desteklenen, saf Python bir kütüphane - pyRF24
gibi C/C++ derlemesi gerektirmiyor, Pi Zero 2W'de kurulumu en az sorunlu
seçenek bu (bkz. SETUP.md).

nRF24 <-> Raspberry Pi Zero 2W kablolama (donanım SPI0):

    nRF24 pin   Pi fiziksel pin   Pi GPIO (BCM)
    ---------   ---------------   -------------
    VCC (3.3V)  17                 -            *** 5V DEĞİL, 3.3V ***
    GND         20                 -
    CE          15                 GPIO22       nRF24'ün kendi RX/TX mod pini
    CSN         24                 GPIO8        SPI0 CE0 (chip select)
    SCK         23                 GPIO11       SPI0 SCLK
    MOSI        19                 GPIO10       SPI0 MOSI
    MISO        21                 GPIO9        SPI0 MISO
    IRQ         -                  -            bağlanmadı, kullanılmıyor

    NOT: nRF24'ün "CE" pini ile Pi'nin SPI "CE0" pini farklı şeylerdir -
    CE0, Pi'nin SPI chip-select hattıdır ve nRF24'ün CSN'ine gider; nRF24'ün
    kendi CE'si ayrı bir GPIO'ya (GPIO22) bağlanır. Karıştırmayın.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# nRF24'te 6 alıcı hattı sınırını aşmamak için tüm cihazlar bu ortak
# adrese yazar; gönderen kimliği paketin içinde (device_id) taşınır.
_COMMON_ADDRESS = b"\xe7\xe7\xe7\xe7\xe7"


class NRF24Radio:
    def __init__(self, rf_channel: int) -> None:
        self.ok = False
        self._nrf = None
        try:
            self._nrf = self._init_hardware(rf_channel)
            self.ok = True
            logger.info("nRF24 başlatıldı (kanal=%d)", rf_channel)
        except Exception as exc:  # donanım yok/kablolanmadı/kütüphane eksik
            logger.warning(
                "nRF24 başlatılamadı, 'radyo yok' modunda devam ediliyor: %s", exc
            )
            self.ok = False

    @staticmethod
    def _init_hardware(rf_channel: int):
        import board
        import digitalio
        from circuitpython_nrf24l01.rf24 import RF24

        ce = digitalio.DigitalInOut(board.D22)
        csn = digitalio.DigitalInOut(board.CE0)
        spi = board.SPI()

        nrf = RF24(spi, csn, ce)

        # circuitpython-nrf24l01 ve ESP32'deki RF24 (TMRh20) kütüphanesinin
        # varsayılanları birbirinden farklı (ör. bu kütüphane dinamik payload'u
        # varsayılan AÇIK tutar, TMRh20 varsayılan KAPALI tutar). Varsayılana
        # güvenmek iki tarafın birbirini hiç duymamasına yol açtı - bu yüzden
        # her ayar burada AÇIKÇA set ediliyor, esp32-node.ino'daki karşılığıyla
        # birebir eşleşmeli.
        nrf.address_length = 5
        nrf.channel = rf_channel
        nrf.dynamic_payloads = False
        nrf.payload_length = 12
        nrf.crc = 2
        nrf.data_rate = 1
        nrf.auto_ack = True

        nrf.open_tx_pipe(_COMMON_ADDRESS)
        nrf.open_rx_pipe(1, _COMMON_ADDRESS)
        nrf.listen = True

        logger.info(
            "nRF24 ayarları: kanal=%d adres_genisligi=%d payload=%d crc=%d "
            "veri_hizi=%dMbps auto_ack=%s dinamik_payload=%s",
            nrf.channel,
            nrf.address_length,
            nrf.payload_length,
            nrf.crc,
            nrf.data_rate,
            bool(nrf.auto_ack),
            bool(nrf.dynamic_payloads),
        )
        return nrf

    def send(self, payload: bytes) -> bool:
        """Tek seferlik gönderim. Retry/timeout mantığı burada YOK - bkz. pending.py."""
        if not self.ok:
            return False
        self._nrf.listen = False
        try:
            return bool(self._nrf.send(payload))
        finally:
            self._nrf.listen = True

    def poll(self) -> Optional[bytes]:
        """Bekleyen bir paket varsa ham baytlarını döner, yoksa None."""
        if not self.ok:
            return None
        if self._nrf.available():
            return bytes(self._nrf.read())
        return None
