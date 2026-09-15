# Akıllı Ev — Durum (2026-09-15)

Repo: https://github.com/kava2019/o-proje (master, 6 commit)

## Ne bitti

- **Mimari onaylandı ve uygulandı**: `pc-server/` (Windows, FastAPI),
  `pi-gateway/` (Pi Zero 2W, Python), `esp32-node/` (Arduino sketch).
  WebSocket mesaj formatları (PC↔tarayıcı, PC↔gateway) ve nRF24 paket
  formatı (`RadioPacket`, 12 byte, little-endian) onaylandı.
- **protocol.py + protocol.h**: yazıldı. Python tarafı kendi içinde
  (struct.pack vs elle hesaplanan bağımsız pack) doğrulandı; gerçek
  çıktısı (`012aaabbccddeeff01020101`) C++ tarafındaki
  `radioPacketSelfTest()`'e elle kopyalandı (bkz. Önemli kısıtlar).
- **pc-server**: tam çalışıyor. REST (`/api/devices`), WS
  (`/ws/gateway`, `/ws/ui`), isimler `devices.json`'a kalıcı, state/type
  bellekte. JWT için `auth.py`'de boş dependency hazır. Radyo/gateway
  hiç yokken tek başına ayağa kalktığı test edildi.
- **pi-gateway**: tam çalışıyor. `radio.py` (nRF24 sürücüsü, donanım
  yoksa `ok=False` ile çökmeden devam eder), `pending.py` (teslim
  garantisi tek yerde, `cmd_timeout_ms`/`cmd_retries` config'den),
  `ws_client.py` (5sn'de bir yeniden bağlanma), `main.py`
  (WHOIS/HELLO/HELLO_ACK/STATUS akışı). `SETUP.md`: SPI açma, pin
  tablosu, systemd, Windows güvenlik duvarı, spi/gpio grup üyeliği.
  **Gerçekten çalıştırılıp doğrulandı**: radio_ok=false senaryosu, 5sn
  reconnect, PC yeniden açılınca otomatik bağlanma.
- **esp32-node**: `esp32-node.ino` yazıldı - tek KURULUM AYARLARI
  bloğu, `radioPacketSelfTest()` boot'ta PASS/FAIL, HELLO/HELLO_ACK/
  CMD/STATUS için Serial logları, `WiFi.macAddress()` ile cihaz
  kimliği, röle boot glitch koruması, `readRelayState()` placeholder'ı.
  `SETUP.md`: nRF24↔ESP32 pin tablosu, Arduino IDE kurulumu.
  **HİÇ derlenmedi** (bkz. Önemli kısıtlar).
- **README.md**: donanımsız uçtan uca test rehberi - 5 senaryo da
  gerçekten çalıştırılıp doğrulandı (pc-server+pi-gateway birlikte,
  "gateway bağlı/radyo yok" banner'ı, `tools/fake_esp.py` ile sahte
  cihaz/isim/komut akışı, gateway kapalıyken 503, PC restart sonrası
  otomatik yeniden bağlanma). Komutlar gerçek Windows PowerShell
  5.1'de test edilip düzeltildi (PYTHONPATH gereksiz, `cp`→`copy`,
  `curl`→`curl.exe` + escape'li JSON).

## Sırada ne var (donanım gelince)

1. `esp32-node.ino`'yu Arduino IDE'de ilk kez derle - `SETUP.md`'deki
   kurulumu takip et. `radioPacketSelfTest()` `FAIL` derse ya da
   derleme hatası çıkarsa **röleyi bağlamadan önce** düzelt.
2. nRF24 modüllerini `pi-gateway/SETUP.md` ve `esp32-node/SETUP.md`'deki
   pin tablolarına göre kabloa (VCC'yi 3.3V'a, 5V'a değil).
3. Pi'de `raspi-config` ile SPI'yi aç, `pi-gateway/config.json`'u
   `config.example.json`'dan kopyalayıp gerçek PC IP'sini yaz.
4. Gerçek radyoyla ilk uçtan uca deneme: tek ESP32 + röle, pc-server
   arayüzünden aç/kapat, `README.md`'deki senaryoları gerçek donanımla
   tekrarla.

## Ertelenen kararlar

- **JWT auth**: `pc-server/app/auth.py`'de boş dependency var, ne
  zaman/nasıl ekleneceği (token formatı, login akışı) belirlenmedi.
- **Röle donanım geri beslemesi**: NC kontağın bir giriş pinine
  bağlanması ertelendi; `readRelayState()` tek fonksiyon olarak hazır,
  donanım gelince sadece o değişecek.
- **Çoklu cihaz ölçekleme**: mimari destekliyor (WHOIS'e cevapta
  device_id'ye göre kademeli gecikme) ama tek simüle cihazdan fazlasıyla
  hiç denenmedi.
- **Röle kartı aktif seviyesi** (`RELAY_ACTIVE_LEVEL=LOW` varsayılan) ve
  **rf_channel/network_id üretim değerleri** (şu an örnek: 76/1) -
  gerçek donanımla doğrulanacak.
- **Hangi ESP32 kartı kullanılacağı netleşmedi**; pin tablosu
  (CE=GPIO4, CSN=GPIO5, VSPI varsayılan SCK/MOSI/MISO=18/23/19) genel
  "ESP32 Dev Module" için - farklı bir kart (C3/S2/S3 vb.) kullanılırsa
  pin ataması gözden geçirilmeli.

## Önemli kısıtlar

- Bu geliştirme ortamında (Windows, Claude Code) **C/C++ derleyicisi
  yok** (g++/clang/cl.exe/arduino-cli hiçbiri kurulu değil).
  `protocol.h`'nin byte dizilimi Python tarafında gerçek çalıştırılıp
  elde edilen hex'in C++ tarafına elle kopyalanmasıyla dolaylı
  doğrulandı; `esp32-node.ino` **hiç derlenmedi**. Gerçek doğrulama ilk
  Arduino IDE derlemesinde/yüklemesinde olacak.
- `adafruit-blinka` bu Windows makinesinde board'u tanımıyor (beklenen
  davranış) - bu sayede pi-gateway'in "radyo yok" modu gerçek
  çalıştırılıp test edilebildi, ama gerçek Pi + nRF24 donanım
  kombinasyonu hiç denenmedi.
