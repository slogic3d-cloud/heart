#include "effects.h"

namespace effects {

using heart::COLS;
using heart::NUM_LEDS;
using heart::ROWS;

static CRGB *L;
static heart::Pos pos[NUM_LEDS];
static uint8_t dist[NUM_LEDS];  // Abstand zur Herzmitte, 0..255

void begin(CRGB *leds) {
  L = leds;
  heart::buildChain(pos);
  float maxd = 0, d[NUM_LEDS];
  for (int i = 0; i < NUM_LEDS; i++) {
    float dx = pos[i].col - 4.0f, dy = pos[i].row - 3.2f;
    d[i] = sqrtf(dx * dx + dy * dy);
    if (d[i] > maxd) maxd = d[i];
  }
  for (int i = 0; i < NUM_LEDS; i++) dist[i] = uint8_t(d[i] / maxd * 255);
}

// Herzschlag ~55 bpm: kräftiger Schlag, kleiner Nachschlag, Pause.
void heartbeat() {
  uint16_t t = millis() % 1100;
  for (int i = 0; i < NUM_LEDS; i++) {
    // äußere LEDs schlagen minimal später -> Welle von innen nach außen
    int tt = int(t) - dist[i] / 4;
    uint8_t v = 0;
    if (tt >= 0 && tt < 160) v = cubicwave8(tt * 255 / 160);
    else if (tt >= 260 && tt < 400) v = cubicwave8((tt - 260) * 255 / 140) * 3 / 4;
    v = qadd8(scale8(v, 230), 18);  // nie ganz aus
    L[i] = CHSV(250, 255, v);
  }
}

void rainbow() {
  uint8_t base = millis() / 12;
  for (int i = 0; i < NUM_LEDS; i++)
    L[i] = CHSV(base + (pos[i].col + pos[i].row) * 14, 255, 255);
}

void ripple() {
  uint8_t phase = millis() / 6;
  uint8_t hue = millis() / 60;
  for (int i = 0; i < NUM_LEDS; i++) {
    uint8_t w = sin8(dist[i] * 2 - phase);
    L[i] = CHSV(hue + dist[i] / 4, 230, scale8(w, w));
  }
}

void sparkle() {
  for (int i = 0; i < NUM_LEDS; i++) L[i] = blend(L[i], CRGB(40, 0, 12), 24);
  if (random8() < 90) L[random8(NUM_LEDS)] = CRGB::White;
  if (random8() < 40) L[random8(NUM_LEDS)] = CHSV(230, 120, 255);
}

void fire() {
  static uint8_t heat[ROWS][COLS];
  static uint32_t last;
  if (millis() - last < 30) return;
  last = millis();
  for (int r = 0; r < ROWS; r++)  // abkühlen
    for (int c = 0; c < COLS; c++) heat[r][c] = qsub8(heat[r][c], random8(10, 60));
  for (int r = 0; r < ROWS - 1; r++)  // Hitze steigt nach oben (Zeile 0 = oben)
    for (int c = 0; c < COLS; c++) {
      int l = c > 0 ? c - 1 : c, rr = c < COLS - 1 ? c + 1 : c;
      int below2 = r + 2 < ROWS ? r + 2 : ROWS - 1;
      heat[r][c] = (heat[r + 1][c] * 2 + heat[r + 1][l] + heat[r + 1][rr] +
                    heat[below2][c] * 2) / 6;
    }
  for (int c = 2; c < 7; c++)  // Funken unten an der Spitze
    if (random8() < 130) heat[ROWS - 1][c] = qadd8(heat[ROWS - 1][c], random8(120, 220));
  for (int r = ROWS - 3; r < ROWS; r++)
    for (int c = 0; c < COLS; c++)
      if (random8() < 25) heat[r][c] = qadd8(heat[r][c], random8(40, 120));
  for (int i = 0; i < NUM_LEDS; i++)
    L[i] = HeatColor(heat[pos[i].row][pos[i].col]);
}

void scanner() {
  // Position in 1/16 Zeilen, läuft hin und her
  uint16_t p = beatsin16(18, 0, (ROWS - 1) * 16);
  uint8_t hue = millis() / 40;
  for (int i = 0; i < NUM_LEDS; i++) {
    int d = abs(int(pos[i].row) * 16 - int(p));
    uint8_t v = d < 24 ? 255 - d * 10 : 0;
    L[i] = blend(L[i], CHSV(hue + pos[i].col * 6, 255, v), 80);
  }
}

void confetti() {
  fadeToBlackBy(L, NUM_LEDS, 12);
  if (random8() < 120) L[random8(NUM_LEDS)] += CHSV(random8(), 200, 255);
}

const Effect LIST[] = {
    {"Herzschlag", heartbeat}, {"Regenbogen", rainbow}, {"Wellen", ripple},
    {"Glitzer", sparkle},      {"Feuer", fire},         {"Scanner", scanner},
    {"Konfetti", confetti},
};
const uint8_t COUNT = sizeof(LIST) / sizeof(LIST[0]);

}  // namespace effects
