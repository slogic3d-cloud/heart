#pragma once
#include <FastLED.h>
#include "heart_map.h"

// Alle Effekte schreiben in leds[] (heart::NUM_LEDS) und werden pro Frame aufgerufen.
namespace effects {

void begin(CRGB *leds);  // einmal in setup()

void heartbeat();   // rot pulsierend, "bum-bum"
void rainbow();     // diagonale Regenbogen-Welle
void ripple();      // Ringe von der Mitte nach außen
void sparkle();     // Glitzern auf rosa Grund
void fire();        // Feuer von unten nach oben
void scanner();     // Farbbalken läuft von oben nach unten
void confetti();    // bunte Konfetti-Punkte

using Fn = void (*)();
struct Effect {
  const char *name;
  Fn fn;
};

extern const Effect LIST[];
extern const uint8_t COUNT;  // ohne Auto-Modus

}  // namespace effects
