// Akilli Ev - ESP32 role node'u.
//
// nRF24 ile gateway'i dinler, komut gelince role pinini surer, role
// durumunu okuyup geri yayinlar. Kendi adini/odasini BILMEZ; sadece
// MAC'inden tureyen device_id ve DEVICE_TYPE_VALUE'yu tasir. Isimlendirme
// sadece PC tarafinda tutulur.
#include <SPI.h>
#include <RF24.h>
#include "protocol.h"

// ==================== KURULUM AYARLARI ====================
// Kart/oda degistiginde SADECE bu blok degisir, kodun geri kalani ayni
// kalir.
#define NETWORK_ID          1            // pi-gateway/config.json .network_id ile AYNI olmali
#define RF_CHANNEL          76           // pi-gateway/config.json .rf_channel ile AYNI olmali
#define RELAY_PIN           26           // rolenin bagli oldugu GPIO
#define RELAY_ACTIVE_LEVEL  LOW          // role karti aktif-LOW ise LOW, aktif-HIGH ise HIGH
#define DEVICE_TYPE_VALUE   DEVICE_LIGHT // DEVICE_PLUG ya da DEVICE_LIGHT (protocol.h)
#define PIN_CE              4           // nRF24 CE
#define PIN_CSN             5           // nRF24 CSN (SPI chip-select)
// =============================================================

// nRF24'te 6 alici hatti sinirini asmamak icin tum cihazlar bu ortak
// adrese yazar; gonderen kimligi paketin icinde (device_id) tasinir.
// pi-gateway/gateway/radio.py'deki _COMMON_ADDRESS ile AYNI olmali.
static const uint8_t COMMON_ADDRESS[5] = {0xE7, 0xE7, 0xE7, 0xE7, 0xE7};

// HELLO onay bekleme: ack gelmeden artan araliklarla (1s,2s,4s,8s'de
// sabitlenir) tekrar denenir. nRF24 yari cift yonlu oldugu icin gateway
// o anda konusuyorsa ilk HELLO'yu kacirabilir.
static const unsigned long HELLO_BACKOFF_MAX_MS = 8000;
// WHOIS'e cevaben HELLO'lar cakismasin diye device_id'ye gore kademeli
// gecikme ust siniri.
static const uint32_t WHOIS_STAGGER_MAX_MS = 200;
// CMD sonrasi STATUS gonderirken cakismayi onlemek icin device_id'ye
// gore kademeli gecikme ust siniri.
static const uint32_t STATUS_STAGGER_MAX_MS = 50;

RF24 radio(PIN_CE, PIN_CSN);

uint8_t myDeviceId[6];
bool helloAcked = false;
unsigned long lastHelloSentAt = 0;
unsigned long helloBackoffMs = 1000;
uint8_t relayStateVar = STATE_OFF;

uint32_t idBasedDelayMs(uint32_t maxMs) {
  // Rastgele sayi ureteci yerine kendi ID'sinden tureyen, deterministik
  // ama cihazdan cihaza farkli bir gecikme: ek koordinasyon gerektirmez.
  return myDeviceId[5] % (maxMs + 1);
}

uint8_t readRelayState() {
  // Su an yazilimsal tutuluyor. Ileride rolenin NC kontagi bir giris
  // pinine baglanip gercek durum okunacak - o zaman SADECE bu fonksiyon
  // degisecek.
  return relayStateVar;
}

void setRelay(uint8_t state) {
  relayStateVar = state;
  digitalWrite(RELAY_PIN, (state == STATE_ON) ? RELAY_ACTIVE_LEVEL : !RELAY_ACTIVE_LEVEL);
}

void sendPacket(const RadioPacket &pkt) {
  uint8_t buf[12];
  radioPacketSerialize(pkt, buf);
  radio.stopListening();
  radio.write(buf, sizeof(buf));
  radio.startListening();
}

void sendHello() {
  RadioPacket pkt;
  pkt.msg_type = MSG_HELLO;
  pkt.network_id = NETWORK_ID;
  memcpy(pkt.device_id, myDeviceId, 6);
  pkt.device_type = DEVICE_TYPE_VALUE;
  pkt.seq = 0;
  pkt.state = STATE_OFF;
  sendPacket(pkt);
  Serial.println("[HELLO] gonderildi");
}

void setup() {
  Serial.begin(115200);
  delay(200); // seri port baglansin diye kisa bekleme

  bool selfTestOk = radioPacketSelfTest();
  Serial.println(selfTestOk ? "[SELFTEST] protocol.h byte dizilimi: PASS"
                            : "[SELFTEST] protocol.h byte dizilimi: FAIL - role baglamadan once duzelt!");

  // Once kapali seviyeye cek, SONRA cikisa al - ters sirada her acilista
  // role bir an ceker.
  digitalWrite(RELAY_PIN, !RELAY_ACTIVE_LEVEL);
  pinMode(RELAY_PIN, OUTPUT);

  // WiFi kullanmadan fabrika MAC'ini efuse'tan oku
  uint64_t efuse = ESP.getEfuseMac();
  for (int i = 0; i < 6; i++) myDeviceId[i] = (efuse >> (8 * i)) & 0xFF;
  Serial.printf("[BOOT] device_id=%02X%02X%02X%02X%02X%02X device_type=%d network_id=%d rf_channel=%d\n",
                myDeviceId[0], myDeviceId[1], myDeviceId[2],
                myDeviceId[3], myDeviceId[4], myDeviceId[5],
                DEVICE_TYPE_VALUE, NETWORK_ID, RF_CHANNEL);

  while (!radio.begin()) {
    Serial.println("[RADIO] nRF24 baslatilamadi (kablolamayi kontrol et), 1sn sonra tekrar denenecek");
    delay(1000);
  }
  radio.setChannel(RF_CHANNEL);
  radio.openWritingPipe(COMMON_ADDRESS);
  radio.openReadingPipe(1, COMMON_ADDRESS);
  radio.startListening();
  Serial.println("[RADIO] nRF24 hazir, dinleme modunda");

  lastHelloSentAt = millis();
  sendHello();
}

void loop() {
  unsigned long now = millis();

  if (!helloAcked && (now - lastHelloSentAt >= helloBackoffMs)) {
    Serial.printf("[HELLO] ack gelmedi, backoff=%lums ile tekrar deneniyor\n", helloBackoffMs);
    sendHello();
    lastHelloSentAt = now;
    helloBackoffMs = min(helloBackoffMs * 2, HELLO_BACKOFF_MAX_MS);
  }

  if (!radio.available()) {
    return;
  }

  uint8_t buf[12];
  radio.read(buf, sizeof(buf));
  RadioPacket pkt;
  radioPacketDeserialize(buf, pkt);

  if (pkt.network_id != NETWORK_ID) {
    return; // baska bir kurulumun paketi, yok say
  }

  if (pkt.msg_type == MSG_WHOIS) {
    Serial.println("[WHOIS] alindi, HELLO ile cevap veriliyor");
    delay(idBasedDelayMs(WHOIS_STAGGER_MAX_MS));
    sendHello();
    lastHelloSentAt = millis();
    return;
  }

  if (memcmp(pkt.device_id, myDeviceId, 6) != 0) {
    return; // baska cihaza yonelik paket
  }

  if (pkt.msg_type == MSG_HELLO_ACK) {
    if (!helloAcked) {
      helloAcked = true;
      Serial.println("[HELLO_ACK] alindi, kayit tamamlandi");
    }
    return;
  }

  if (pkt.msg_type == MSG_CMD) {
    Serial.printf("[CMD] alindi seq=%u state=%u\n", pkt.seq, pkt.state);
    setRelay(pkt.state);
    delay(idBasedDelayMs(STATUS_STAGGER_MAX_MS));

    RadioPacket status;
    status.msg_type = MSG_STATUS;
    status.network_id = NETWORK_ID;
    memcpy(status.device_id, myDeviceId, 6);
    status.device_type = DEVICE_TYPE_VALUE;
    status.seq = pkt.seq;
    status.state = readRelayState();
    sendPacket(status);
    Serial.printf("[STATUS] gonderildi seq=%u state=%u\n", status.seq, status.state);
  }
}
