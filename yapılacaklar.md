# Akıllı Ev — Durum (2026-09-23)

Repo: https://github.com/kava2019/o-proje (master)

## Ne bitti

- **Faz 1-2** (esp32-node ilk derleme/yükleme, pi-gateway gerçek Pi'de
  PC'ye bağlanma) — önceki devirde bitti, bkz. eski commit'ler.
- **Faz 3 — nRF24 kablolama**: donanım her iki tarafta da çalışır hale
  geldi (Pi'de "nRF24 başlatıldı", ESP'de "[HELLO] gonderildi") ama iki
  taraf birbirini hiç duymuyordu.
- **Kök neden bulundu**: `circuitpython-nrf24l01` (Pi) dinamik payload'u
  varsayılan AÇIK tutuyor, `RF24`/TMRh20 (ESP32) varsayılan KAPALI
  tutuyor — bu asimetri paketin PCF/CRC hesabını iki tarafta farklı
  yorumlatıp paketlerin sessizce reddedilmesine yol açıyordu.
- **Düzeltme uygulandı**: `pi-gateway/gateway/radio.py` ve
  `esp32-node/esp32-node.ino`'da payload boyutu (12 byte sabit), CRC,
  veri hızı, adres genişliği, auto-ack artık iki tarafta da açıkça set
  ediliyor; ikisi de boot'ta bu ayarları loglar (Pi: `logger.info`, ESP:
  `Serial.printf`) — ileride tekrar uyuşmazlık çıkarsa iki log yan yana
  konup kütüphane kaynak koduna bakmadan karşılaştırılabilsin diye.
- **Faz 4 — gerçek donanımla uçtan uca doğrulandı**: ESP'de
  "[HELLO_ACK] alindi, kayit tamamlandi", "[CMD] alindi seq=1 state=1",
  "[STATUS] gonderildi seq=1 state=1" göründü; tarayıcıdan gönderilen
  komut ESP'ye ulaştı, röle durumu geri geldi. İki tarafın ayar logları
  birebir eşleşiyor.

## Sırada ne var

1. **Çoklu cihaz**: şu ana kadar tek ESP32 + röle ile doğrulandı;
   birden fazla node aynı ağda (WHOIS'e kademeli gecikmeli cevap
   mekanizması) hiç denenmedi.
2. **Röle donanım geri beslemesi**: NC kontağın bir giriş pinine
   bağlanması hâlâ ertelendi; `readRelayState()` yazılımsal state
   tutmaya devam ediyor.
3. **Üretim değerleri**: `rf_channel`/`network_id` (şu an örnek: 76/1)
   ve `RELAY_ACTIVE_LEVEL` gerçek röle kartına göre doğrulanacak.

## Ertelenen kararlar

- **JWT auth**: `pc-server/app/auth.py`'de boş dependency var, ne
  zaman/nasıl ekleneceği belirlenmedi.
- **Hangi ESP32 kartı kullanılacağı netleşmedi**; pin tablosu (CE=GPIO4,
  CSN=GPIO5, VSPI varsayılan SCK/MOSI/MISO=18/23/19) genel "ESP32 Dev
  Module" için — farklı bir kart (C3/S2/S3 vb.) kullanılırsa pin ataması
  gözden geçirilmeli.

## Önemli kısıtlar

- Bu geliştirme ortamında (Windows, Claude Code) hâlâ **C/C++
  derleyicisi yok**; `esp32-node.ino`'daki değişiklikler yalnızca
  gerçek Arduino IDE'de, gerçek donanımda derlenip doğrulanabiliyor —
  Faz 4'teki doğrulama tamamen sizin tarafınızda yapıldı.
