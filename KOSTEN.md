# Kosten – LED-Herz

Stand: **12.10.2026 13:15** · Wechselkurs: 1 $ = 0.8926 € (Mon, 12 Oct 2026 00:02:32 +0000)  
Erzeugt mit `python3 tools/kosten.py --boards 2`. Bauteilpreise und Kurs sind live abgefragt, Werte mit *Schätzung* bitte selbst prüfen.

## Zusammenfassung

| Posten | Kosten |
|---|---|
| Platinen von JLCPCB (2 bestückt, 5 gefertigt, inkl. Versand) | **63,77 €** |
| Selbst zu kaufen (XIAO, Leisten, Taster, Elko, Schrauben, Netzteil) – pro Herz | **17,70 €** |
| Filament (verbrauchte Menge) | **3,36 €** |
| Filament (zu kaufen: 1 Rolle à 1 kg) | 15,99 € |
| **Ein fertiges Herz, alles zusammen** (Platinen-Bestellung + Teile + 1 Rolle Filament) | **97,46 €** |

Pro Herz gerechnet (Platinenkosten durch 2 geteilt): ca. **52,94 €**.

## Filament: Anycubic PLA+ rot, gedruckt auf dem Anycubic Kobra 2 Neo

| Teil | Verbrauch | Druckzeit |
|---|---|---|
| Rückschale | 89 g | 3 h 43 min |
| Pixel-Gitter | 58 g | 3 h 55 min |
| Diffusor | 22 g | 51 min |
| Ständer | 41 g | 1 h 35 min |
| Tasterstößel | 1 g | 9 min |
| **Summe** | **210 g** | **ca. 10 h** |
| + 15 % Reserve (Fehldrucke, Reinigen) | 241 g |

**→ 1 Rolle (1 kg) reicht** – danach bleiben ca. 759 g übrig.

Geslict mit den offiziellen Anycubic-Profilen für den **Kobra 2 Neo** (0,4-mm-Düse, „0.20mm Standard“: 2 Wände, 3 Schichten oben/unten, 15 % Füllung, 5-mm-Rand; Filament „Anycubic PLA“, Dichte 1,24 g/cm³). Die Profile stammen aus OrcaSlicer, auf dem der Anycubic Slicer Next basiert, und sind in `cad/slicer_kobra2neo.ini` für PrusaSlicer übersetzt. Im Anycubic Slicer selbst können Gramm und Zeit leicht abweichen. Alle Teile passen auf das 220 × 220-mm-Bett. Tipp: Gitter in **Schwarz** und Diffusor in **Weiß** sehen besser aus – dann brauchst du rot nur 130 g.

## JLCPCB: Bauteile (live von LCSC, für 2 Platinen)

| Teil | LCSC | pro Platine | Menge | Stückpreis | Summe | Lager | Typ |
|---|---|---|---|---|---|---|---|
| 100nF 50V X7R 0603 | C14663 | 47 | 94 | 0,0142 $ | 1,33 $ | 200 | Basic |
| 10uF 25V X5R 0805 | C15850 | 1 | 2 | 0,0695 $ | 0,14 $ | 0 | Basic |
| 330R 1% 0603 | C23138 | 1 | 2 | 0,0026 $ | 0,01 $ | 764.500 | Basic |
| 5.1k 1% 0603 | C23186 | 2 | 4 | 0,0015 $ | 0,01 $ | 19.278.000 | Basic |
| SN74AHCT1G125DBVR | C7484 | 1 | 2 | 0,1009 $ | 0,20 $ | 26.835 | Extended |
| SS34 Schottky 40V 3A SMA | C408258 | 1 | 2 | 0,0402 $ | 0,08 $ | 72.900 | Extended |
| HRO TYPE-C-31-M-12 | C165948 | 1 | 2 | 0,1879 $ | 0,38 $ | 378.915 | Extended |
| WS2812B-B/W 5050 RGB LED | C114586 | 46 | 92 | 0,0841 $ | 7,74 $ | 324.520 | Extended |
| **Summe Bauteile** | | | | | **9,88 $** | | |

JLCPCB rechnet eigene Teilepreise (plus ein paar Ersatzteile); LCSC-Preise sind ein guter Richtwert. Der Lagerbestand ist der von LCSC – JLCPCB hat ein eigenes Lager, das zeigt der Bauteil-Check beim Bestellen.

## JLCPCB: Bestückung (Economic PCBA)

| Posten | Kosten |
|---|---|
| Einrichtung | 8,18 $ |
| Schablone | 1,53 $ |
| 618 Lötstellen × 0,0016 $ | 0,99 $ |
| 4 Extended-Teile × 3,07 $ Ladegebühr | 12,28 $ |
| ggf. Handlöten (Gehäuselaschen der USB-C-Buchse) | 3,58 $ |
| **Summe Bestückung** | **26,56 $** |

Platinenfläche ca. 247 cm² – unter 650 cm², also **kein** Großformat-Aufschlag.

## JLCPCB: Leiterplatte und Versand (*Schätzung*)

| Posten | Kosten |
|---|---|
| 5 × Leiterplatte 2 Lagen, 162 × 153 mm | ca. 20,00 $ *Schätzung* |
| Versand nach Deutschland | ca. 15,00 $ *Schätzung* |

Den echten Preis zeigt der JLCPCB-Rechner, sobald du `heart_gerber.zip` hochlädst. Werte in `tools/kosten.py` (PCB_5PCS_USD_ESTIMATE, SHIPPING_USD_ESTIMATE) eintragen und neu ausführen.
Bei Bestellungen aus China kommt ggf. Einfuhrumsatzsteuer dazu (JLCPCB zeigt sie meist schon im Warenkorb an).

## Selbst zu kaufen (pro Herz, Richtwerte)

| Teil | Menge | Preis | Summe | Quelle |
|---|---|---|---|---|
| Seeed XIAO ESP32-C3 | 1 | 6,05 € | 6,05 € | z. B. OpenELAB, Okt. 2026 |
| Buchsenleiste 1x7, 2,54 mm | 2 | 0,40 € | 0,80 € | Richtwert |
| Taster 6x6 mm THT | 1 | 0,20 € | 0,20 € | Richtwert |
| Elko 1000 µF / 10 V, Ø10 mm | 1 | 0,35 € | 0,35 € | Richtwert |
| Schrauben 2,9 x 9,5 mm (Kunststoff/Blech) | 3 | 0,10 € | 0,30 € | Richtwert |
| USB-C-Netzteil 5 V / 3 A | 1 | 10,00 € | 10,00 € | Richtwert, falls keins vorhanden |
| **Summe** | | | **17,70 €** | |

