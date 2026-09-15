// nRF24 radyo paketi.
//
// Byte dizilimi pi-gateway/gateway/protocol.py ile birebir aynı olmak
// zorunda: little-endian, 1+1+6+1+2+1 = 12 byte, padding yok.
//
//   msg_type    uint8   MSG_* sabitlerinden biri
//   network_id  uint8   kurulum kimligi (asagida #define ile)
//   device_id   6 byte  ESP32 MAC adresi (ham byte, endianness yok)
//   device_type uint8   DEVICE_* sabitlerinden biri
//   seq         uint16  CMD/STATUS eslestirme sira numarasi
//   state       uint8   STATE_* sabitlerinden biri
//
// ESP32 (Xtensa/RISC-V) zaten little-endian oldugu icin uint16_t alan
// (seq) icin ekstra byte-swap gerekmez.
#pragma once

#include <stdint.h>
#include <string.h>

// --- msg_type ---
static const uint8_t MSG_CMD = 0x01;
static const uint8_t MSG_STATUS = 0x02;
static const uint8_t MSG_HELLO = 0x03;
static const uint8_t MSG_WHOIS = 0x04;
static const uint8_t MSG_HELLO_ACK = 0x05;

// --- device_type ---
static const uint8_t DEVICE_PLUG = 0x00;
static const uint8_t DEVICE_LIGHT = 0x01;

// --- state ---
static const uint8_t STATE_OFF = 0x00;
static const uint8_t STATE_ON = 0x01;

struct __attribute__((packed)) RadioPacket {
  uint8_t msg_type;
  uint8_t network_id;
  uint8_t device_id[6];
  uint8_t device_type;
  uint16_t seq;
  uint8_t state;
};

static_assert(sizeof(RadioPacket) == 12,
              "RadioPacket 12 byte olmali - protocol.py ile hizasi bozuldu");

inline void radioPacketSerialize(const RadioPacket &pkt, uint8_t out[12]) {
  memcpy(out, &pkt, sizeof(RadioPacket));
}

inline void radioPacketDeserialize(const uint8_t in[12], RadioPacket &pkt) {
  memcpy(&pkt, in, sizeof(RadioPacket));
}

// pi-gateway/gateway/protocol.py icindeki SELFTEST_PACKET ile ayni degerler.
// Asagidaki `expected` dizisi elle hesaplanmadi: bu makinede calistirilan
//   python pi-gateway/gateway/protocol.py
// komutunun GERCEK ciktisindan (012aaabbccddeeff01020101) birebir kopyalandi.
// Bu ortamda C++ derleyicisi olmadigi icin bu fonksiyon burada calistirilamadi;
// ESP32'ye ilk derleme/yukleme sirasinda setup() icinden cagirip Serial'a
// PASS/FAIL basacagiz - iki tarafin gercekten ayni bayt dizilimini
// urettigini o an dogrulamis olacagiz.
inline bool radioPacketSelfTest() {
  RadioPacket pkt;
  pkt.msg_type = MSG_CMD;
  pkt.network_id = 0x2A;
  const uint8_t id[6] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF};
  memcpy(pkt.device_id, id, 6);
  pkt.device_type = DEVICE_LIGHT;
  pkt.seq = 0x0102;
  pkt.state = STATE_ON;

  uint8_t out[12];
  radioPacketSerialize(pkt, out);

  // python protocol.py ciktisi: 01 2a aa bb cc dd ee ff 01 02 01 01
  static const uint8_t expected[12] = {0x01, 0x2A, 0xAA, 0xBB, 0xCC, 0xDD,
                                        0xEE, 0xFF, 0x01, 0x02, 0x01, 0x01};

  if (memcmp(out, expected, 12) != 0) {
    return false;
  }

  RadioPacket roundtrip;
  radioPacketDeserialize(out, roundtrip);
  return memcmp(&roundtrip, &pkt, sizeof(RadioPacket)) == 0;
}
