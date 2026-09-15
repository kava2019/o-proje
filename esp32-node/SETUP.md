# esp32-node kurulumu

## 1. nRF24 ↔ ESP32 kablolama

| nRF24 pin  | ESP32 pin (GPIO)      |
|------------|-----------------------|
| VCC (3.3V) | 3V3                   |
| GND        | GND                   |
| CE         | GPIO4                 |
| CSN        | GPIO5                 |
| SCK        | GPIO18 (VSPI SCK)      |
| MOSI       | GPIO23 (VSPI MOSI)     |
| MISO       | GPIO19 (VSPI MISO)     |
| IRQ        | bağlanmadı             |

CE/CSN pinleri `esp32-node.ino` içindeki `PIN_CE`/`PIN_CSN` ile eşleşmeli
(değiştirirsen ikisini birden değiştir). SCK/MOSI/MISO, ESP32'nin
donanım SPI (VSPI) hattı olduğu için sabittir.

**VCC'yi 3.3V'a bağla, 5V'a DEĞİL** — nRF24L01 5V ile kalıcı hasar
görür.

## 2. Arduino IDE - ESP32 kart paketi

1. `Dosya > Tercihler` (File > Preferences) açılır.
2. "Ek Kart Yöneticisi URL'leri" (Additional Boards Manager URLs) alanına:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. `Araçlar > Kart > Kart Yöneticisi` (Tools > Board > Boards Manager),
   "esp32" ara, **esp32 by Espressif Systems** paketini kur.

## 3. Kütüphane kurulumu

`Araçlar > Kütüphane Yönet` (Tools > Manage Libraries):

- **RF24** (yazar: TMRh20) ara ve kur.

Başka bir nRF24 kütüphanesi kurma — pi-gateway tarafında kullanılan
`circuitpython-nrf24l01` ile API'si farklı ama paket formatı (protocol.h)
aynı; burada TMRh20/RF24 kullanılıyor çünkü ESP32 Arduino ortamında fiili
standart ve aktif bakımlı.

## 4. Kart ve port seçimi

`Araçlar > Kart > esp32` altından kullandığın gerçek ESP32 kartını seç
(ör. "ESP32 Dev Module"). Kart bilgisayara USB ile takılıyken:

- `Araçlar > Port`: kartın göründüğü COM portu seç (Windows'ta
  Aygıt Yöneticisi > Bağlantı Noktaları'ndan hangi COM olduğunu
  görebilirsin).
- `Araçlar > Upload Speed`: 921600 çalışmazsa 115200'e düşür.

`esp32-node.ino`'yu aç, üstteki KURULUM AYARLARI bloğunu (özellikle
`DEVICE_TYPE_VALUE` ve gerekirse `RELAY_PIN`/`RELAY_ACTIVE_LEVEL`) bu
karta göre ayarla, yükle.

## 5. İlk açılışta ne görmen lazım

Seri port monitörünü (115200 baud) aç:

```
[SELFTEST] protocol.h byte dizilimi: PASS
[BOOT] device_id=AABBCCDDEEFF device_type=1 network_id=1 rf_channel=76
[RADIO] nRF24 hazir, dinleme modunda
[HELLO] gonderildi
```

`SELFTEST` `FAIL` derse **röleyi bağlamadan önce** protocol.h'nin iki
tarafta (bu dosya ve pi-gateway/gateway/protocol.py) hizadan çıktığı
anlamına gelir — devam etme.

`[HELLO] ack gelmedi, backoff=...` tekrar tekrar görünüyorsa gateway ya
çalışmıyordur ya da radyo/kablolama sorunu vardır; pi-gateway
loglarında (`journalctl -u smart-home-gateway -f`) karşılık gelen bir
`[WHOIS]`/HELLO trafiği olup olmadığına bak.
