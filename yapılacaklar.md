Onaylıyorum, değişiklikleri yap. Ek olarak:

Her iki tarafta da başlangıçta bu ayarları LOGLA — payload boyutu, CRC,
veri hızı, adres genişliği, auto-ack, kanal. Pi başlarken bunları INFO
olarak bassın, ESP de boot'ta Serial'a yazsın.

Böylece bir daha ayar uyuşmazlığı olursa iki logu yan yana koyup 10
saniyede görürüm, tekrar kütüphane kaynak kodu okumam gerekmez.

Sonra commit ve push et.