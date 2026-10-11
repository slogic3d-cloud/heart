// LED-Herz – Lichtshow mit 46 WS2812B und einem Taster
//
// Taster kurz drücken  -> nächster Effekt (nach dem letzten kommt "Auto")
// Taster lang drücken  -> Helligkeit durchschalten
// Effekt und Helligkeit bleiben nach dem Ausstecken gespeichert.
#include <Arduino.h>
#include <FastLED.h>
#include <Preferences.h>

#include "config.h"
#include "effects.h"
#include "heart_map.h"

static CRGB leds[heart::NUM_LEDS];
static Preferences prefs;

static uint8_t mode;        // 0..COUNT-1 = fester Effekt, COUNT = Auto-Modus
static uint8_t autoIndex;   // aktueller Effekt im Auto-Modus
static uint8_t brightLevel;
static uint32_t lastAutoSwitch;

static const uint8_t NUM_LEVELS = sizeof(BRIGHTNESS_LEVELS);

static void save() {
  prefs.putUChar("mode", mode);
  prefs.putUChar("bright", brightLevel);
}

static void showModeName() {
  if (mode == effects::COUNT)
    Serial.println("Modus: Auto");
  else
    Serial.printf("Modus: %s\n", effects::LIST[mode].name);
}

// Entprellter Taster: liefert 1 = kurz, 2 = lang, 0 = nichts
static uint8_t readButton() {
  static bool stable = HIGH, lastRaw = HIGH, longFired = false;
  static uint32_t changedAt = 0, pressedAt = 0;
  bool raw = digitalRead(BUTTON_PIN);
  uint32_t now = millis();
  if (raw != lastRaw) {
    lastRaw = raw;
    changedAt = now;
  }
  if (now - changedAt < DEBOUNCE_MS) return 0;
  if (raw != stable) {
    stable = raw;
    if (stable == LOW) {
      pressedAt = now;
      longFired = false;
    } else if (!longFired) {
      return 1;
    }
  }
  if (stable == LOW && !longFired && now - pressedAt > LONG_PRESS_MS) {
    longFired = true;
    return 2;
  }
  return 0;
}

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, heart::NUM_LEDS)
      .setCorrection(TypicalLEDStrip);
  FastLED.setMaxPowerInVoltsAndMilliamps(POWER_VOLTS, POWER_MILLIAMPS);

  prefs.begin("heart", false);
  mode = prefs.getUChar("mode", 0);
  brightLevel = prefs.getUChar("bright", DEFAULT_BRIGHTNESS_LEVEL);
  if (mode > effects::COUNT) mode = 0;
  if (brightLevel >= NUM_LEVELS) brightLevel = DEFAULT_BRIGHTNESS_LEVEL;
  FastLED.setBrightness(BRIGHTNESS_LEVELS[brightLevel]);

  effects::begin(leds);

  // Kurzer Selbsttest: jede LED einmal der Reihe nach (zeigt Lötfehler sofort)
  for (int i = 0; i < heart::NUM_LEDS; i++) {
    leds[i] = CHSV(i * 255 / heart::NUM_LEDS, 255, 255);
    FastLED.show();
    delay(15);
  }
  FastLED.clear();

  Serial.println("LED-Herz bereit <3");
  showModeName();
}

void loop() {
  switch (readButton()) {
    case 1:
      mode = (mode + 1) % (effects::COUNT + 1);
      autoIndex = 0;
      lastAutoSwitch = millis();
      FastLED.clear();
      save();
      showModeName();
      break;
    case 2:
      brightLevel = (brightLevel + 1) % NUM_LEVELS;
      FastLED.setBrightness(BRIGHTNESS_LEVELS[brightLevel]);
      save();
      Serial.printf("Helligkeit: %u\n", BRIGHTNESS_LEVELS[brightLevel]);
      break;
  }

  uint8_t fx = mode;
  if (mode == effects::COUNT) {
    if (millis() - lastAutoSwitch > AUTO_SWITCH_SECONDS * 1000UL) {
      lastAutoSwitch = millis();
      autoIndex = (autoIndex + 1) % effects::COUNT;
    }
    fx = autoIndex;
  }

  EVERY_N_MILLISECONDS(1000 / FRAMES_PER_SECOND) {
    effects::LIST[fx].fn();
    FastLED.show();
  }
}
