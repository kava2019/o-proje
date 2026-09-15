Yapıyı onaylıyorum. Kodu yazmadan önce şu 7 maddeyi ekle:

Yapıyı onaylıyorum. Kodu yazmadan önce şu 6 maddeyi ekle:

1. HELLO kaybolma sorunu
   Gateway PC'ye bağlı değilken açılan ESP'nin HELLO'su kaybolur ve
   cihaz görünmez kalır. İki ek:
   a) Gateway PC'ye (yeniden) bağlandığında tüm cihazlara bir WHOIS
      yayını yapsın (msg_type 0x04), cihazlar HELLO ile cevaplasın.
      Cevaplar device_id'ye göre kademeli gecikmeyle gelsin.
   b) ESP tek HELLO atıp susmasın. Gateway'den onay gelmezse artan
      aralıklarla (1s, 2s, 4s, 8s) tekrar denesin, onay gelince sussun.
      nRF24 yarı çift yönlü; gateway o anda konuşuyorsa ilk HELLO'yu
      duymaz.

2. Kayıtlı cihazdan HELLO gelirse ismi SIFIRLAMA
   PC sadece "online" işaretlesin. Elektrik kesintisi sonrası tüm
   cihazlar HELLO atacak, kullanıcının verdiği isimler uçmamalı.

3. Paket hizalama
   RadioPacket hem Python hem C++ tarafında birebir aynı byte dizilimi
   olmalı. C++ tarafında __attribute__((packed)) kullan, Python tarafında
   struct formatını explicit little-endian ('<') yaz. Derleyici padding'i
   eklerse iki taraf birbirini anlamaz. Paket boyutunu her iki tarafta
   assert ile doğrula.

4. Ağ kimliği ve kanal
   Pakete 1 byte network_id ekle, config'den gelsin. Farklı ID'li
   paketleri ESP ve gateway atsın. Ayrıca RF kanalı config'den
   ayarlanabilir olsun. Komşuda aynı sistem varsa cihazlarımızı
   kumanda edemesin.

5. Gateway çevrimdışıyken komut
   Kullanıcı butona bastığında gateway bağlı değilse PC komutu kuyruğa
   ALMASIN, 503 dönsün ve arayüz bunu göstersin. Sessizce yutulan komut
   en kötü davranış.

6. ESP boot'ta röle tetiklenmesi
   setup() içinde önce digitalWrite(RELAY_PIN, KAPALI_SEVIYE), SONRA
   pinMode(RELAY_PIN, OUTPUT). Ters sırada her açılışta röle bir an
   çeker. Röle kartı aktif-LOW ise KAPALI_SEVIYE HIGH olur; bunu tek bir
   #define ile üstte tanımla, kart tipine göre değiştirebileyim.

7. Röle geri beslemesi (şimdi değil, yer bırak)
   Röle durumu şu an yazılımsal tutuluyor. İleride rölenin NC kontağı
   bir giriş pinine bağlanıp gerçek durum okunacak. ESP'de durumu
   döndüren tek bir fonksiyon olsun (readRelayState() gibi), şimdilik
   değişkeni döndürsün. Böylece donanım geri beslemesi eklenince
   sadece o fonksiyon değişsin.