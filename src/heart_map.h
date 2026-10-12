#pragma once
// Herz-Matrix: welche LED (Index in der Datenkette) sitzt an welcher Stelle?
// MUSS mit hardware/gen_pcb.py (MASK + chain_order) übereinstimmen.
// Keine Arduino-Abhängigkeiten, damit es auch am PC getestet werden kann.
#include <stdint.h>

namespace heart {

constexpr int COLS = 9;
constexpr int ROWS = 8;

// 'X' = LED, '.' = keine LED. Zeile 0 ist oben.
constexpr const char *MASK[ROWS] = {
    ".XX...XX.",
    "XXXX.XXXX",
    "XXXXXXXXX",
    "XXXXXXXXX",
    ".XXXXXXX.",
    "..XXXXX..",
    "...XXX...",
    "....X....",
};

// rekursiv, damit es auch mit C++11-Compilern (ESP32-Arduino) geht
constexpr int countRow(const char *s) { return *s ? (*s == 'X') + countRow(s + 1) : 0; }
constexpr int countLeds(int r = 0) { return r < ROWS ? countRow(MASK[r]) + countLeds(r + 1) : 0; }

constexpr int NUM_LEDS = countLeds();  // 46

// Position jeder LED in der Kette
struct Pos {
  int8_t col, row;
};

// Kette: Start unten an der Spitze, dann Schlangenlinie nach oben.
// Zeile k (von unten gezählt): gerade k = links->rechts, ungerade = rechts->links.
inline void buildChain(Pos *out) {
  int i = 0;
  for (int k = 0; k < ROWS; k++) {
    int r = ROWS - 1 - k;
    bool ltr = (k % 2) == 0;
    for (int j = 0; j < COLS; j++) {
      int c = ltr ? j : COLS - 1 - j;
      if (MASK[r][c] == 'X') out[i++] = {int8_t(c), int8_t(r)};
    }
  }
}

}  // namespace heart
