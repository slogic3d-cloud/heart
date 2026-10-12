# Einkaufsliste – Links (Deutschland)

Stand: 12.10.2026 18:22. Nur **BerryBase** und **Amazon (Versand durch Amazon)**, dazu JLCPCB für die Platine.

## 1. Platine (fertig bestückt)

| Was | Wo | Hinweis |
|---|---|---|
| Leiterplatte + Bestückung | [JLCPCB Online-Angebot](https://jlcpcb.com/quote) | `hardware/production/heart_gerber.zip` hochladen, dann BOM + CPL (siehe README) |

## 2. BerryBase (alles in einer Bestellung)

| Teil | Menge | Link | Verfügbar | Hinweis |
|---|---|---|---|---|
| Buchsenleiste 1x40, RM 2,54, gerade | 1 | [BerryBase](https://www.berrybase.de/buchsenleiste-1x-40-polig-rm-2-54-gerade) | lieferbar | Mit dem Seitenschneider 2 × 7 Pins abschneiden (Sockel für den XIAO). |
| Kurzhubtaster 6x6 mm, THT, H 4,3 mm | 2 | [BerryBase](https://www.berrybase.de/kurzhubtaster-vertikale-printmontage-6x6mm-h-4-3mm) | lieferbar | Taster „EFFEKT“. 1 Ersatz. Funktioniert mit dem Tasterstößel aus dem Gehäuse. |
| Elko 1000 µF / 25 V, Ø10 × 20 mm, RM 5 mm | 1 | [BerryBase](https://www.berrybase.de/elektrolytkondensator-1000-f-25v-1050c-1-radial-tht) | lieferbar | C50. Passt: Ø10 mm, Raster 5 mm, 20 mm hoch (22 mm Platz im Gehäuse). Polung beachten! |
| Raspberry Pi USB-C-Netzteil 5,1 V / 3 A | 1 | [BerryBase](https://www.berrybase.de/offizielles-raspberry-pi-usb-c-netzteil-5-1v-3-0a-eu-weiss) | lieferbar | Stromversorgung fürs Herz. Weglassen, wenn du schon ein USB-C-Netzteil mit 3 A hast. |

## 3. Amazon (nur Angebote mit „Versand durch Amazon“)

| Teil | Menge | Link | Hinweis |
|---|---|---|---|
| Seeed Studio XIAO ESP32-C3 | 1 | [Amazon-Suche](https://www.amazon.de/s?k=Seeed+Studio+XIAO+ESP32C3) | Steckt hinten auf der Platine. Ohne Stiftleisten ist ok, die lötest du an (liegen meist bei). |
| Anycubic PLA+ Filament, Rot, 1 kg, 1,75 mm | 1 | [Amazon-Suche](https://www.amazon.de/s?k=Anycubic+PLA%2B+Filament+1kg+rot) | Für Gehäuse, Gitter, Diffusor, Ständer: 210 g (1 Rolle reicht). |
| Blechschrauben-Sortiment (2,9 × 9,5 mm) | 1 | [Amazon-Suche](https://www.amazon.de/s?k=Blechschrauben+Sortiment+2%2C9+x+9%2C5) | Du brauchst 3 Stück (Platine in die Abstandshalter). Alternativ M3 × 8 mm. |

**So findest du „Versand durch Amazon“:** In der Amazon-Suche links den Filter **Prime** setzen. Auf der Produktseite rechts im Kaufkasten muss bei **Versand** „Amazon“ stehen (Verkäufer darf ein anderer sein). Steht dort ein anderer Versender: nicht nehmen.

Die Amazon-Links sind Suchlinks, weil Amazon automatische Abfragen blockt. Ich konnte dort Preise und Versandart nicht selbst prüfen. Schau vor dem Kauf genau hin:

- **XIAO:** Es muss wirklich „Seeed Studio XIAO ESP32C3“ sein (21 × 17,8 mm). Der XIAO ESP32-S3 passt auch (gleiche Pins, Firmware unterstützt ihn).
- **PLA+:** Marke Anycubic, 1,75 mm, 1 kg, Farbe Rot.

