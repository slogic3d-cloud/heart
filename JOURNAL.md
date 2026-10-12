# Journal – LED-Herz

Ein herzförmiges PCB mit 46 RGB-LEDs (WS2812B), einem Seeed XIAO ESP32-C3 und einem Taster,
das Lichtshows abspielt. Dazu ein 3D-gedrucktes Gehäuse mit Pixel-Gitter und ein Ständer.

**Phase:** Design
**Gesamtzeit:** 1,7 h

> Hinweis: Das Projekt habe ich zusammen mit dem KI-Assistenten Claude (Claude Code) gemacht.
> Ich habe die Entscheidungen getroffen (was gebaut wird, Bauteile, Bestückung, Größe, Gehäuse),
> Claude hat dabei Code, Platinen-Skripte und Doku geschrieben.

---

## 11.10.2026 – Idee, Planung und Entscheidungen

**Zeit:** 0,2 h

Ich will ein Herz aus LEDs, das Lichtshows abspielt. Und ich will endlich mal ein **eigenes PCB** machen,
statt LEDs auf Pappe zu kleben.

Entscheidungen:
- **ESP32** als Controller: schnell, billig, per USB programmierbar. Genommen: **Seeed XIAO ESP32-C3**,
  klein, USB-C drauf, steckt auf Buchsenleisten hinten auf der Platine (wieder abziehbar).
- **WS2812B-LEDs**, jede LED kann einzeln jede Farbe, nur damit gehen richtige Lichtshows.
- **46 LEDs** als Herz-Matrix (9 × 8 Raster, 16 mm Abstand) → das Herz wird ca. 16 × 15 cm groß.
- **JLCPCB bestückt** die SMD-Teile (46 LEDs + 47 Kondensatoren von Hand wäre zu viel).
- **Ein Taster**: kurz drücken = nächster Effekt, lang = Helligkeit.
- **Strom über eine eigene USB-C-Buchse** (5 V), nicht über den XIAO.

Die LED-Anordnung (X = LED):

```
.XX...XX.
XXXX.XXXX
XXXXXXXXX
XXXXXXXXX
.XXXXXXX.
..XXXXX..
...XXX...
....X....
```

![Effekte in der Vorschau](https://raw.githubusercontent.com/slogic3d-cloud/heart-/main/docs/preview_rainbow.png)

---

## 11.10.2026 – Platine designen (KiCad)

**Zeit:** 0,5 h

Die ganze Platine wird von einem Python-Skript (`hardware/gen_pcb.py`) in KiCad erzeugt:
Herzumriss, 46 LEDs mit je einem 100-nF-Kondensator, die Datenleitung als Kette von LED zu LED,
USB-C-Buchse, Pegelwandler, XIAO-Sockel, Taster, Elko.

Was ich gelernt habe:
- Der ESP32 gibt **3,3 V** aus, WS2812B bei 5 V wollen eigentlich mind. 3,5 V → **Pegelwandler 74AHCT1G125**.
- Jede WS2812B braucht einen **100 nF** direkt daneben.
- **Kupferflächen** statt dicker Leiterbahnen: Vorderseite komplett +5V, Rückseite komplett GND.
- **USB-C** braucht zwei **5,1 kΩ** an CC1/CC2, sonst gibt das Netzteil keinen Strom.
- Eine **Schottky-Diode** vor dem XIAO verhindert, dass der Laptop beim Flashen alle LEDs versorgen muss.

Was schiefging:
1. Die mathematische Herzkurve hatte oben eine super tiefe Kerbe und unten eine zu schmale Spitze,
   da liefen Leitungen über den Rand. → Neue Herzform aus **zwei Kreisbögen + 45°-Flanken**.
   Die unteren LED-Reihen bilden eh eine 45°-Treppe, das passt perfekt.
2. Die Zeilenwechsel der LED-Kette liefen außen herum über den Rand → jetzt **schräg auf der Treppe**.
3. Eine Leitung war nur **0,16 mm** von einem Pad weg (erlaubt: 0,2 mm) → mittig zwischen die Pads gelegt.
4. USB-C-Buchse erst an einer Geraden links → Stufe im Herz, sah doof aus. → Jetzt **schräg auf der Flanke unten links**.
5. Der **1000-µF-Elko** stand direkt vor der USB-Buchse des XIAO, man hätte kein Kabel einstecken können!
   → Auf die andere Seite verschoben.

Ergebnis: **DRC 0 Fehler, 0 offene Verbindungen.** Bestelldateien für JLCPCB (Gerber, BOM, CPL)
in `hardware/production/`, alle LCSC-Teilenummern bei LCSC nachgeprüft.

![Platine Vorderseite](https://raw.githubusercontent.com/slogic3d-cloud/heart-/main/docs/pcb_front.png)

![Platine Rückseite](https://raw.githubusercontent.com/slogic3d-cloud/heart-/main/docs/pcb_back.png)

---

## 11.10.2026 – Firmware, Vorschau und Doku

**Zeit:** 0,3 h

- Firmware mit **FastLED** (PlatformIO): 7 Effekte (Herzschlag, Regenbogen, Wellen, Glitzer, Feuer,
  Scanner, Konfetti) + Auto-Modus. Taster kurz/lang, Einstellungen bleiben gespeichert.
- Die Firmware kennt die Reihenfolge der LEDs auf der Platine (Start an der Spitze, Schlangenlinie nach oben),
  damit z. B. das Feuer wirklich von unten nach oben brennt. Ein **Test** prüft, dass Firmware
  und Platine dieselbe Reihenfolge haben (46/46 ok).
- **Browser-Vorschau** (`tools/preview.html`), damit ich die Effekte ohne Hardware sehen kann.
  Das Feuer war erst viel zu hell (nur gelb/weiß) → Abkühlung und Funken angepasst.
- README mit Bestell-, Löt- und Flash-Anleitung.

![Feuer-Effekt in der Vorschau](https://raw.githubusercontent.com/slogic3d-cloud/heart-/main/docs/preview_fire.png)

---

## 11.10.2026 – Schaltplan in KiCad

**Zeit:** 0,3 h

- Richtigen **KiCad-Schaltplan** `hardware/heart.kicad_sch` gebaut, mit den Symbolen aus der
  KiCad-Bibliothek und einem eigenen Symbol für den XIAO.
- Verbunden über **Netzlabels**, die genauso heißen wie die Leitungen auf der Platine.
- Schaltplan und Platine sind **verknüpft**, „Leiterplatte aus Schaltplan aktualisieren“ (F8) funktioniert.
- Prüfskript lässt KiCad die Netzliste exportieren und vergleicht **jeden Pin** mit der Platine:
  106 Bauteile, 54 Netze, 328 Pins, alles gleich.

Problem: KiCad wollte die erste Version nicht öffnen, weil das Skript die Reihenfolge von Einträgen
in der Datei vertauscht hat. Reihenfolge beibehalten, dann ging's.

![Schaltplan](https://raw.githubusercontent.com/slogic3d-cloud/heart-/main/docs/schematic_kicad.png)

---

## 12.10.2026 – Gehäuse und Ständer (Fusion 360 / 3D-Druck)

**Zeit:** 0,4 h

- Gehäuse mit **CadQuery** (CAD in Python) gebaut, Export als **STEP für Fusion 360** und STL zum Drucken:
  - **Rückschale** mit Abstandshaltern, Schlitz für die USB-C-Buchse, Fenster fürs XIAO-USB-Kabel,
    Loch für den Tasterstößel, 2 Schlüssellöcher zum Aufhängen
  - **Pixel-Gitter** (16-mm-Raster), damit jede LED ein eigenes Quadrat beleuchtet
  - **Diffusor** (1 mm), **Tasterstößel** und **Ständer** mit 90°-V-Tasche für die Herzspitze
- **Kollisionsprüfung**: Platine, XIAO, Elko, Taster und USB-Buchse als Platzhalter, kein Teil kollidiert.

Probleme:
- Das erste Gitter war fast massiv: 79 cm³ Material → durchgehendes Raster, nur noch 47 cm³.
- Der Umriss bestand aus 240 kleinen Geraden → riesige STEP-Dateien mit Facetten in Fusion.
  → Echte Kreisbögen, Dateien bis zu 40× kleiner.
- Die USB-C-Buchse steht 1,1 mm über den Platinenrand → Schlitz in der Wand nach oben offen,
  sonst bekommt man die Platine nicht rein.

![Explosionszeichnung](https://raw.githubusercontent.com/slogic3d-cloud/heart-/main/docs/case_exploded.png)

![Im Ständer](https://raw.githubusercontent.com/slogic3d-cloud/heart-/main/docs/case_stand.png)

---

## Nächste Schritte (Build-Phase)

- [ ] Platine bei JLCPCB bestellen (Bauteil-Drehung in der Vorschau prüfen!)
- [ ] XIAO ESP32-C3, Buchsenleisten, Taster, Elko besorgen
- [ ] Gehäuse bei einem Druckdienst bestellen
- [ ] Löten, flashen, testen, Video von der Lichtshow
