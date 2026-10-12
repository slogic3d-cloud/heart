#!/usr/bin/env python3
"""
Kostenaufstellung mit aktuellen Preisen erzeugen:

    python3 tools/kosten.py            # 2 bestückte Platinen (Minimum bei JLCPCB)
    python3 tools/kosten.py --boards 5

- Bauteilpreise: live von LCSC (dieselben Teile, die JLCPCB bestückt)
- Wechselkurs USD -> EUR: live von open.er-api.com
- Filament: aus PrusaSlicer (Einstellungen in cad/slicer_pla.ini)
- alles andere: feste Richtwerte, unten in FIXED – bitte bei Bedarf anpassen

Schreibt KOSTEN.md ins Hauptverzeichnis.
"""
import argparse
import csv
import datetime
import json
import math
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOM = os.path.join(ROOT, "hardware", "production", "heart_bom.csv")
OUT = os.path.join(ROOT, "KOSTEN.md")

# Lötstellen pro Footprint (für die Bestückungskosten)
JOINTS = {"LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm": 4, "C_0603_1608Metric": 2,
          "R_0603_1608Metric": 2, "C_0805_2012Metric": 2, "SOT-23-5": 5, "D_SMA": 2,
          "USB_C_Receptacle_HRO_TYPE-C-31-M-12": 16}
BASIC = {"C14663", "C15850", "C23186", "C23138"}  # JLC-Basic-Teile (keine Ladegebühr)

# JLCPCB Economic PCBA, laut jlcpcb.com/help/article/pcb-assembly-price (Okt. 2026), in USD
JLC = {"setup": 8.18, "stencil": 1.53, "per_joint": 0.0016, "extended": 3.07, "hand_solder": 3.58}
# Leiterplatte 2 Lagen, 162 x 153 mm, 5 Stück: SCHÄTZUNG – echten Preis im JLC-Rechner prüfen!
PCB_5PCS_USD_ESTIMATE = 20.0
SHIPPING_USD_ESTIMATE = 15.0

# Filament (PrusaSlicer, 0,2 mm, 3 Wände, 15 % Gyroid, Dichte 1,24 g/cm³)
FILAMENT_G = {"Rückschale": 94.46, "Pixel-Gitter": 57.77, "Diffusor": 21.04,
              "Ständer": 46.47, "Tasterstößel": 0.62}
PRINT_HOURS = 9.16 + 6.56 + 3.01 + 3.70 + 0.16
FILAMENT_EUR_PER_KG = 15.99   # Anycubic PLA+ 1 kg rot (Preisvergleich, Okt. 2026)
FILAMENT_WASTE = 0.15         # Reserve für Fehldrucke/Reinigen

# Selbst zu kaufen (Richtwerte in EUR, pro Herz)
FIXED = [
    ("Seeed XIAO ESP32-C3", 1, 6.05, "z. B. OpenELAB, Okt. 2026"),
    ("Buchsenleiste 1x7, 2,54 mm", 2, 0.40, "Richtwert"),
    ("Taster 6x6 mm THT", 1, 0.20, "Richtwert"),
    ("Elko 1000 µF / 10 V, Ø10 mm", 1, 0.35, "Richtwert"),
    ("Schrauben 2,9 x 9,5 mm (Kunststoff/Blech)", 3, 0.10, "Richtwert"),
    ("USB-C-Netzteil 5 V / 3 A", 1, 10.00, "Richtwert, falls keins vorhanden"),
]


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "heart-kosten/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def lcsc_price(code, qty):
    d = get_json(f"https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={code}")["result"]
    ladder = sorted(d["productPriceList"], key=lambda p: p["ladder"])
    order_qty = max(qty, ladder[0]["ladder"])
    price = ladder[0]["usdPrice"]
    for p in ladder:
        if order_qty >= p["ladder"]:
            price = p["usdPrice"]
    return price, d.get("stockNumber", 0), d.get("productModel", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boards", type=int, default=2, help="Anzahl bestückter Platinen (min. 2)")
    n = max(2, ap.parse_args().boards)

    fx = get_json("https://open.er-api.com/v6/latest/USD")
    usd_eur = fx["rates"]["EUR"]
    fx_date = fx.get("time_last_update_utc", "")
    now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    rows, parts_usd, joints, ext = [], 0.0, 0, 0
    with open(BOM) as f:
        for r in csv.DictReader(f):
            code, refs = r["LCSC Part #"], r["Designator"].split(",")
            qty = len(refs) * n
            unit, stock, model = lcsc_price(code, qty)
            parts_usd += unit * qty
            joints += JOINTS[r["Footprint"]] * len(refs) * n
            ext += code not in BASIC
            rows.append((r["Comment"], code, len(refs), qty, unit, unit * qty, stock,
                         "Basic" if code in BASIC else "Extended"))

    assy_usd = (JLC["setup"] + JLC["stencil"] + joints * JLC["per_joint"]
                + ext * JLC["extended"] + JLC["hand_solder"])
    pcb_total_usd = PCB_5PCS_USD_ESTIMATE + parts_usd + assy_usd + SHIPPING_USD_ESTIMATE
    pcb_total_eur = pcb_total_usd * usd_eur

    fil_g = sum(FILAMENT_G.values())
    fil_need = fil_g * (1 + FILAMENT_WASTE)
    rolls = math.ceil(fil_need / 1000)
    fil_eur_used = fil_g / 1000 * FILAMENT_EUR_PER_KG

    fixed_eur = sum(q * p for _, q, p, _ in FIXED)
    eur = lambda v: f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")  # noqa: E731
    de = lambda t: t.replace(",", "X").replace(".", ",").replace("X", ".")  # noqa: E731
    usd = lambda v, d=2: de(f"{v:,.{d}f}") + " $"  # noqa: E731

    L = [f"# Kosten – LED-Herz", "",
         f"Stand: **{now}** · Wechselkurs: 1 $ = {usd_eur:.4f} € ({fx_date})  ",
         f"Erzeugt mit `python3 tools/kosten.py --boards {n}`. Bauteilpreise und Kurs sind live abgefragt, "
         f"Werte mit *Schätzung* bitte selbst prüfen.", "",
         "## Zusammenfassung", "",
         "| Posten | Kosten |", "|---|---|",
         f"| Platinen von JLCPCB ({n} bestückt, 5 gefertigt, inkl. Versand) | **{eur(pcb_total_eur)}** |",
         f"| Selbst zu kaufen (XIAO, Leisten, Taster, Elko, Schrauben, Netzteil) – pro Herz | **{eur(fixed_eur)}** |",
         f"| Filament (verbrauchte Menge) | **{eur(fil_eur_used)}** |",
         f"| Filament (zu kaufen: {rolls} Rolle à 1 kg) | {eur(rolls * FILAMENT_EUR_PER_KG)} |",
         f"| **Ein fertiges Herz, alles zusammen** (Platinen-Bestellung + Teile + {rolls} Rolle Filament) | "
         f"**{eur(pcb_total_eur + fixed_eur + rolls * FILAMENT_EUR_PER_KG)}** |", "",
         f"Pro Herz gerechnet (Platinenkosten durch {n} geteilt): "
         f"ca. **{eur(pcb_total_eur / n + fixed_eur + fil_eur_used)}**.", "",
         "## Filament: Anycubic PLA+ rot", "",
         "| Teil | Verbrauch |", "|---|---|"]
    L += [f"| {k} | {v:.0f} g |" for k, v in FILAMENT_G.items()]
    L += [f"| **Summe** | **{fil_g:.0f} g** |",
          f"| + {int(FILAMENT_WASTE * 100)} % Reserve (Fehldrucke, Reinigen) | {fil_need:.0f} g |", "",
          f"**→ {rolls} Rolle (1 kg) reicht** – danach bleiben ca. {rolls * 1000 - fil_need:.0f} g übrig.",
          f"Druckzeit insgesamt ca. {PRINT_HOURS:.0f} h (PrusaSlicer-Schätzung, je nach Drucker anders).", "",
          "Werte aus PrusaSlicer mit `cad/slicer_pla.ini` (0,2 mm Schicht, 3 Wände, 15 % Gyroid, "
          "Dichte 1,24 g/cm³). Tipp: Gitter in **Schwarz** und Diffusor in **Weiß** sehen besser aus – "
          f"dann brauchst du rot nur {FILAMENT_G['Rückschale'] + FILAMENT_G['Ständer'] + FILAMENT_G['Tasterstößel']:.0f} g.", "",
          f"## JLCPCB: Bauteile (live von LCSC, für {n} Platinen)", "",
          "| Teil | LCSC | pro Platine | Menge | Stückpreis | Summe | Lager | Typ |",
          "|---|---|---|---|---|---|---|---|"]
    L += [f"| {c} | {code} | {per} | {q} | {usd(u, 4)} | {usd(t)} | {de(f'{s:,}')} | {typ} |"
          for c, code, per, q, u, t, s, typ in rows]
    L += [f"| **Summe Bauteile** | | | | | **{usd(parts_usd)}** | | |", "",
          "JLCPCB rechnet eigene Teilepreise (plus ein paar Ersatzteile); LCSC-Preise sind ein guter Richtwert. "
          "Der Lagerbestand ist der von LCSC – JLCPCB hat ein eigenes Lager, das zeigt der Bauteil-Check beim Bestellen.", "",
          "## JLCPCB: Bestückung (Economic PCBA)", "",
          "| Posten | Kosten |", "|---|---|",
          f"| Einrichtung | {usd(JLC['setup'])} |",
          f"| Schablone | {usd(JLC['stencil'])} |",
          f"| {joints} Lötstellen × {usd(JLC['per_joint'], 4)} | {usd(joints * JLC['per_joint'])} |",
          f"| {ext} Extended-Teile × {usd(JLC['extended'])} Ladegebühr | {usd(ext * JLC['extended'])} |",
          f"| ggf. Handlöten (Gehäuselaschen der USB-C-Buchse) | {usd(JLC['hand_solder'])} |",
          f"| **Summe Bestückung** | **{usd(assy_usd)}** |", "",
          "Platinenfläche ca. 247 cm² – unter 650 cm², also **kein** Großformat-Aufschlag.", "",
          "## JLCPCB: Leiterplatte und Versand (*Schätzung*)", "",
          "| Posten | Kosten |", "|---|---|",
          f"| 5 × Leiterplatte 2 Lagen, 162 × 153 mm | ca. {usd(PCB_5PCS_USD_ESTIMATE)} *Schätzung* |",
          f"| Versand nach Deutschland | ca. {usd(SHIPPING_USD_ESTIMATE)} *Schätzung* |", "",
          "Den echten Preis zeigt der JLCPCB-Rechner, sobald du `heart_gerber.zip` hochlädst. "
          "Werte in `tools/kosten.py` (PCB_5PCS_USD_ESTIMATE, SHIPPING_USD_ESTIMATE) eintragen und neu ausführen.",
          "Bei Bestellungen aus China kommt ggf. Einfuhrumsatzsteuer dazu (JLCPCB zeigt sie meist schon im Warenkorb an).", "",
          "## Selbst zu kaufen (pro Herz, Richtwerte)", "",
          "| Teil | Menge | Preis | Summe | Quelle |", "|---|---|---|---|---|"]
    L += [f"| {name} | {q} | {eur(p)} | {eur(q * p)} | {src} |" for name, q, p, src in FIXED]
    L += [f"| **Summe** | | | **{eur(fixed_eur)}** | |", ""]
    with open(OUT, "w") as f:
        f.write("\n".join(L) + "\n")
    print(f"OK: {OUT}")
    print(f"  Filament: {fil_g:.0f} g (+Reserve {fil_need:.0f} g) -> {rolls} Rolle(n)")
    print(f"  JLCPCB gesamt ca. {eur(pcb_total_eur)}, selbst kaufen {eur(fixed_eur)}")


if __name__ == "__main__":
    main()
