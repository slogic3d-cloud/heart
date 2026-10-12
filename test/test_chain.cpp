// Prüft am PC, dass die Firmware-LED-Reihenfolge exakt der Platine entspricht.
//   g++ -std=c++11 -Isrc test/test_chain.cpp -o /tmp/test_chain && /tmp/test_chain
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include "heart_map.h"

int main() {
  static_assert(heart::NUM_LEDS == 46, "Herz sollte 46 LEDs haben");
  heart::Pos pos[heart::NUM_LEDS];
  heart::buildChain(pos);

  std::ifstream f("hardware/chain_order.txt");
  if (!f) { std::puts("FEHLER: hardware/chain_order.txt fehlt (gen_pcb.py laufen lassen)"); return 1; }
  std::string line;
  int n = 0, bad = 0;
  bool seen[heart::ROWS][heart::COLS] = {};
  while (std::getline(f, line)) {
    if (line.empty() || line[0] == '#') continue;
    std::istringstream ss(line);
    int i, c, r;
    ss >> i >> c >> r;
    if (i >= heart::NUM_LEDS || pos[i].col != c || pos[i].row != r) {
      std::printf("Abweichung bei LED %d: Platine (%d,%d)\n", i, c, r);
      bad++;
    }
    if (seen[r][c]) { std::printf("doppelt: (%d,%d)\n", c, r); bad++; }
    seen[r][c] = true;
    n++;
  }
  if (n != heart::NUM_LEDS) { std::printf("Anzahl: Platine %d, Firmware %d\n", n, heart::NUM_LEDS); bad++; }
  std::printf("%s: %d LEDs geprüft\n", bad ? "FEHLGESCHLAGEN" : "OK", n);
  return bad ? 1 : 0;
}
