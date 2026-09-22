# Akıllı Ev

Bileşenler: `pc-server/` (Windows, FastAPI), `pi-gateway/` (Raspberry Pi
Zero 2W, Python), `esp32-node/` (Arduino sketch). Kurulum detayları
`pi-gateway/SETUP.md` ve `esp32-node/SETUP.md`'de.

Bu dosya, **donanım (nRF24, Pi, ESP32) elinize gelene kadar** tüm
sistemi tek Windows PC üzerinde uçtan uca deneme adımlarını anlatır.
`pc-server` ve `pi-gateway` aynı makinede, `127.0.0.1` üzerinden
konuşacak şekilde çalıştırılır.

## 1. pc-server ve pi-gateway'i radyo olmadan aynı anda çalıştırma

Bir terminalde pc-server:

```powershell
cd pc-server
python -m venv .venv                                       # ilk seferde
./.venv/Scripts/python -m pip install -r requirements.txt   # ilk seferde
./.venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`PYTHONPATH` ayarlamana gerek yok: `python -m uvicorn ...` çalışma
dizinini (`pc-server/`) zaten otomatik olarak `sys.path`'e ekliyor, bu
yüzden `app.main:app` içe aktarımı ek ayar gerektirmeden çalışıyor.

`--host 0.0.0.0` şart: onsuz uvicorn varsayılan olarak sadece
`127.0.0.1`'i dinler ve gerçek `pi-gateway` (ayrı bir Pi'den) bağlanamaz.

İkinci bir terminalde pi-gateway:

```powershell
cd pi-gateway
python -m venv .venv                                        # ilk seferde
./.venv/Scripts/python -m pip install -r requirements.txt   # ilk seferde
copy config.example.json config.json
# config.json içinde pc_host'u "127.0.0.1", pc_port'u 8000 yap
./.venv/Scripts/python -m gateway.main
```

Bu makinede gerçek bir nRF24/Blinka donanımı olmadığı için gateway
başlarken şunu basar ve **çökmez**:

```
WARNING gateway.radio: nRF24 başlatılamadı, 'radyo yok' modunda devam ediliyor: ...
INFO gateway.ws_client: PC'ye bağlanıldı: ws://127.0.0.1:8000/ws/gateway
INFO __main__: WHOIS yayınlandı (radio_ok=False)
```

## 2. Tarayıcıda "gateway bağlı, radyo yok" durumunu görme

Tarayıcıda aç: `http://127.0.0.1:8000/`

Üstte turuncu/kırmızı bir bantta **"Gateway bağlı, radyo yok"** yazmalı
(pc-server, gateway'den gelen `radio_status: {radio_ok:false}`
mesajını bu banda çeviriyor). Cihaz listesi boş görünür - henüz hiçbir
"ESP" kendini bildirmedi.

## 3. Sahte ESP scripti ile HELLO/STATUS enjekte etme

pc-server aynı anda tek bir gateway bağlantısı kabul eder, bu yüzden
önce 1. adımdaki gerçek `pi-gateway`'i durdur (o terminalde Ctrl+C).

`tools/fake_esp.py`, pi-gateway'in yerine geçip pc-server'ın
`/ws/gateway` ucuna doğrudan bağlanır ve gerçek bir ESP'nin
HELLO/STATUS'unun tetiklediği `announce`/`status` mesajlarını gönderir.
`websockets` paketi pc-server'ın venv'inde zaten kurulu, onu kullan:

```powershell
cd tools
../pc-server/.venv/Scripts/python fake_esp.py --device-id aabbccddeeff --type LIGHT
```

Tarayıcıyı yenile (ya da açık bırak, WS ile anlık gelir):

- Cihaz listesinde **"Cihaz-ddeeff"** adında, "açık/kapalı" durumunda
  bir satır belirmeli.
- İsim kutusuna yeni bir isim yazıp Enter'a bas; `pc-server/devices.json`
  dosyasında (`cat pc-server/devices.json`) kalıcı olarak yazıldığını
  gör.
- **Aç/Kapat** butonuna bas: `fake_esp.py`'nin çalıştığı terminalde
  `[PC'den geldi] {'type': 'command', ...}` ve ~0.2 saniye sonra
  `[gönderildi] status state=...` görünmeli; tarayıcıdaki durum ve
  buton metni gerçekten değişmeli.

## 4. Gateway'i kapatıp komut gönderince 503 alma

`fake_esp.py`'yi (ya da hangisi çalışıyorsa gerçek pi-gateway'i)
Ctrl+C ile durdur. Tarayıcıda üst bant **"Gateway bağlı değil"**'e
döner ve Aç/Kapat butonları pasifleşir (JS bilerek engelliyor) - bu
yüzden 503'ü doğrudan REST ile tetikle:

```powershell
curl.exe -i -X POST http://127.0.0.1:8000/api/devices/aabbccddeeff/command -H "Content-Type: application/json" -d '{\"state\":\"on\"}'
```

**Neden `curl.exe` ve neden `\"` şeklinde escape:** Windows PowerShell'de
`curl` gerçek curl değil, `Invoke-WebRequest`'e giden bir alias'tır ve
`-X`/`-d`/`-H` gibi parametreleri anlamaz (deneyip gördüm - direkt
`ParameterBindingException` hatası veriyor); bu yüzden gerçek programı
çağırmak için `curl.exe` yazmak şart. `-d '{"state":"on"}'` gibi düz tek
tırnaklı JSON da PowerShell'in native programlara argüman aktarımında
bozuluyor (`"Expecting property name enclosed in double quotes"` hatası
gördüm) - `\"` ile escape edince doğru gidiyor.

Beklenen: `HTTP/1.1 503 Service Unavailable` ve gövdede
`{"detail":"gateway bağlı değil"}`. Komut kuyruğa alınmaz, sessizce
yutulmaz.

## 5. PC'yi kapatıp açınca gateway'in kendiliğinden geri bağlanması

1. adımdaki gerçek `pi-gateway` çalışırken pc-server'ı durdur
(o terminalde Ctrl+C). Gateway'in terminalinde ~5 saniyede bir:

```
WARNING gateway.ws_client: PC bağlantısı kurulamadı/koptu: ...
```

görünmeye devam etmeli (gateway kendini kapatmaz, denemeye devam
eder). pc-server'ı aynı komutla tekrar başlat; birkaç saniye içinde
gateway terminalinde:

```
INFO gateway.ws_client: PC'ye bağlanıldı: ws://127.0.0.1:8000/ws/gateway
INFO __main__: WHOIS yayınlandı (radio_ok=False)
```

tekrar görünmeli ve tarayıcıdaki "Gateway bağlı değil" bandı kalkmalı -
elle hiçbir şey yeniden başlatmana gerek kalmadan.
