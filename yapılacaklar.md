README'de iki Windows uyumsuzluğu var, düzelt:
- PYTHONPATH=. bash sözdizimi. Windows karşılığını yaz (ya da gerekli
  değilse kaldır).
- cp yerine copy kullan, ya da hem CMD hem PowerShell karşılığını ver.
Evet, ama tek commit yerine mantıklı parçalara ayır:
- protocol (protocol.py + protocol.h)
- pc-server
- pi-gateway + SETUP.md
- esp32-node + SETUP.md
- README + tools/fake_esp.py

Commit mesajları Türkçe ya da İngilizce, fark etmez ama açıklayıcı olsun.
Sonra GitHub'a push et.
