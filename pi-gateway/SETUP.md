# pi-gateway kurulumu (Raspberry Pi Zero 2W)

## 1. SPI'yi etkinleştirme

Raspberry Pi OS'de SPI **varsayılan olarak kapalı** gelir. nRF24 modülü
SPI üzerinden konuştuğu için önce açılması gerekir.

Menüden:

```
sudo raspi-config
```
`3 Interface Options` -> `I4 SPI` (bazı sürümlerde sadece `SPI`) ->
"Would you like the SPI interface to be enabled?" -> **Yes** -> `Finish`,
sonra yeniden başlat:

```
sudo reboot
```

Menüye girmeden, tek komutla (script/otomasyon için):

```
sudo raspi-config nonint do_spi 0
sudo reboot
```

Etkinleştiğini doğrula (reboot sonrası):

```
ls /dev/spidev*
```
`/dev/spidev0.0` ve `/dev/spidev0.1` görünmeli. Görünmüyorsa SPI hâlâ
kapalı demektir.

## 2. nRF24 ↔ Pi Zero 2W kablolama

| nRF24 pin  | Pi fiziksel pin | Pi GPIO (BCM) |
|------------|------------------|---------------|
| VCC (3.3V) | 17               | -             |
| GND        | 20               | -             |
| CE         | 15               | GPIO22        |
| CSN        | 24               | GPIO8 (SPI0 CE0) |
| SCK        | 23               | GPIO11 (SPI0 SCLK) |
| MOSI       | 19               | GPIO10 (SPI0 MOSI) |
| MISO       | 21               | GPIO9 (SPI0 MISO) |
| IRQ        | bağlanmadı       | -             |

**VCC'yi 3.3V'a bağla, 5V'a DEĞİL** — nRF24L01 modülleri 5V ile kalıcı
hasar görür. nRF24, Pi'nin 3.3V hattından yeterince akım çekemeyip
kararsız çalışabiliyor; sorun yaşarsan modülün VCC-GND arasına 10-100µF
bir kapasitör eklemek yaygın bir çözüm.

## 3. Bağımlılıkları kurma

```
cd pi-gateway
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. config.json

`config.json` gerçek ayarlarla (özellikle PC'nin IP'si) diske yazılır ve
`.gitignore`'dadır — repo'ya girmez. Şablon `config.example.json`'dan
kopyalanır:

```
cp config.example.json config.json
nano config.json
```

```json
{
  "pc_host": "192.168.1.50",
  "pc_port": 8000,
  "network_id": 1,
  "rf_channel": 76,
  "cmd_timeout_ms": 500,
  "cmd_retries": 2
}
```

- `pc_host` / `pc_port`: pc-server'ın çalıştığı Windows PC'nin IP'si ve
  portu (uvicorn `--port` ile neyi verdiysen o).
- `network_id`: bu kuruluma özgü 0-255 arası bir sayı; komşuda aynı
  sistem varsa farklı bir değer ver.
- `rf_channel`: 0-125 arası nRF24 kanalı; WiFi/Bluetooth ile çakışma
  olursa değiştir.
- `cmd_timeout_ms` / `cmd_retries`: teslimat garantisi zaman aşımı ve
  tekrar sayısı (bkz. `gateway/pending.py`) — sahada ayar gerekirse
  sadece burası değişir, kod değişmez.

## 5. Servisi başlatma

Elle, test için:

```
cd pi-gateway
source .venv/bin/activate
python -m gateway.main
```

Kalıcı (systemd) servis olarak:

```
sudo cp smart-home-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now smart-home-gateway
sudo systemctl status smart-home-gateway
journalctl -u smart-home-gateway -f
```

`smart-home-gateway.service` içindeki `WorkingDirectory` ve `ExecStart`
yollarını kendi kurulum yoluna göre düzenle (repo'yu `/home/kava/o-proje`
dışına klonladıysan).

## 6. Windows güvenlik duvarı

Pi, PC'ye pc-server'ın dinlediği porttan (varsayılan **8000**) bağlanır.
Windows ilk çalıştırmada uvicorn için gelen bağlantıyı engeller ve
gateway "PC bağlantısı kurulamadı" diyerek 5 saniyede bir sonsuz
denemeye girer; sebebi genelde budur.

PC'de **yönetici olarak açılmış** bir PowerShell'de:

```powershell
New-NetFirewallRule -DisplayName "Akilli Ev PC Server" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private
```

`-Profile Private` ev ağını varsayar; PC farklı bir ağ profilindeyse
(`Get-NetConnectionProfile` ile kontrol edilebilir) `-Profile Any`
kullanılabilir. pc-server'ı farklı bir portla çalıştırıyorsan
(`PC_SERVER_PORT`), `-LocalPort` değerini ona göre değiştir.

## 7. Blinka'nın SPI erişimi (spi/gpio grupları)

Raspberry Pi OS'de SPI cihazına (`/dev/spidev0.0`) erişim genelde `spi`
ve `gpio` gruplarına üyeliğe bağlıdır; kullanıcı bu gruplarda değilse
Blinka izin hatasıyla "radyo yok" moduna düşer (uygulama çökmez ama
donanım hiç konuşamaz).

Mevcut grupları kontrol et:

```
groups
```

`spi` ve `gpio` listede yoksa ekle:

```
sudo usermod -aG spi,gpio $USER
```

Bu değişikliğin etkili olması için **çıkış yapıp tekrar giriş yapman ya
da yeniden başlatman** gerekir (`sudo reboot`). Sonra tekrar `groups`
ile doğrula.
