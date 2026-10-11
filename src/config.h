#pragma once
#include <Arduino.h>

// ---------------------------------------------------------------------------
// Hier alles einstellen, was zu deinem Aufbau passt.
// ---------------------------------------------------------------------------

#if defined(ARDUINO_XIAO_ESP32C3) || defined(ARDUINO_XIAO_ESP32S3)
  // Die Herz-Platine: XIAO steckt hinten, Pins wie im Layout
  #define LED_PIN     D10   // -> 74AHCT1G125 -> 330R -> erste LED (Spitze)
  #define BUTTON_PIN  D2    // Taster "EFFEKT" gegen GND
#else
  // ESP32 DevKit auf dem Steckbrett
  #define LED_PIN     16
  #define BUTTON_PIN  4
#endif

#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB          // Falls Rot und Grün vertauscht sind: RGB probieren

// Stromlimit (5V). 46 LEDs voll weiß wären ~2,8 A – das begrenzen wir.
// Mit einem 3A-USB-C-Netzteil kannst du auf 2500 gehen.
#define POWER_VOLTS       5
#define POWER_MILLIAMPS   1500

// Helligkeitsstufen (Taster lang drücken schaltet durch)
static const uint8_t BRIGHTNESS_LEVELS[] = { 24, 64, 128, 200 };
#define DEFAULT_BRIGHTNESS_LEVEL 1

#define FRAMES_PER_SECOND   60
#define AUTO_SWITCH_SECONDS 15   // Auto-Modus: so oft wechselt der Effekt

#define LONG_PRESS_MS 800
#define DEBOUNCE_MS   30
