# Akıllı Ev - Proje Durumu

## Faz 1 - esp32-node (bitti)

- `esp32-node.ino` ilk kez derlendi ve yüklendi.
- `radioPacketSelfTest` PASS.
- `device_id`, MAC ile eşleşti (`8C94DF8CAC38`).
- WiFi kütüphanesi kaldırıldı, MAC artık `ESP.getEfuseMac()` ile okunuyor.

## Faz 2 - pi-gateway (bitti)

- Gateway gerçek Pi'de çalıştı, PC'ye bağlandı.
- Tarayıcıda "Gateway bağlı, radyo yok" göründü.
- Pi'de SPI açıldı.
- Kod, git clone ile deploy key üzerinden indirildi.
- Windows'ta hotspot ağı Public geliyor; firewall kuralı Private için
  yazıldığından ağı Private'a çevirmek gerekti.

## Faz 3 - nRF24 kablolama (sırada)

- Dişi-dişi jumper kablo bekleniyor.
