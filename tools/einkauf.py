#!/usr/bin/env python3
"""
Einkaufsliste mit aktuellen Preisen erzeugen:

    python3 tools/einkauf.py            # 2 bestückte Platinen (Minimum bei JLCPCB)
    python3 tools/einkauf.py --boards 5

Schreibt:
    einkauf/links.md   alle Kauflinks (Deutschland: BerryBase, Amazon mit Versand durch Amazon, JLCPCB)
    einkauf/price.md   alle Preise in Euro und Dollar

Live abgefragt: BerryBase-Preise + Verfügbarkeit, LCSC-Bauteilpreise (für JLCPCB),
Wechselkurs USD/EUR, Referenzpreise (Anycubic-Shop, OpenELAB) für die Amazon-Artikel.
Amazon selbst blockt automatische Abfragen – dort den Preis beim Kauf prüfen.
"""
import argparse
import csv
import datetime
import json
import math
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOM = os.path.join(ROOT, "hardware", "production", "heart_bom.csv")
OUTDIR = os.path.join(ROOT, "einkauf")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/141 Safari/537.36"

# ---------------------------------------------------------------------------
# Was du selbst kaufst (pro Herz)
# shop: "berrybase" -> Preis/Verfügbarkeit live von der Produktseite
#       "amazon"    -> Suchlink, Preis = Referenzpreis (ref_url live, sonst ref_eur)
# ---------------------------------------------------------------------------
ITEMS = [
    {"name": "Seeed Studio XIAO ESP32-C3", "qty": 1, "shop": "amazon",
     "url": "https://www.amazon.de/s?k=Seeed+Studio+XIAO+ESP32C3",
     "ref": ("OpenELAB", "https://openelab.io/de/products/seeed-studio-xiao-esp32c3.js", None), "ref_eur": 6.85,
     "note": "Steckt hinten auf der Platine. Ohne Stiftleisten ist ok, die lötest du an (liegen meist bei)."},
    {"name": "Buchsenleiste 1x40, RM 2,54, gerade", "qty": 1, "shop": "berrybase",
     "url": "https://www.berrybase.de/buchsenleiste-1x-40-polig-rm-2-54-gerade",
     "note": "Mit dem Seitenschneider 2 × 7 Pins abschneiden (Sockel für den XIAO)."},
    {"name": "Kurzhubtaster 6x6 mm, THT, H 4,3 mm", "qty": 2, "shop": "berrybase",
     "url": "https://www.berrybase.de/kurzhubtaster-vertikale-printmontage-6x6mm-h-4-3mm",
     "note": "Taster „EFFEKT“. 1 Ersatz. Funktioniert mit dem Tasterstößel aus dem Gehäuse."},
    {"name": "Elko 1000 µF / 25 V, Ø10 × 20 mm, RM 5 mm", "qty": 1, "shop": "berrybase",
     "url": "https://www.berrybase.de/elektrolytkondensator-1000-f-25v-1050c-1-radial-tht",
     "note": "C50. Passt: Ø10 mm, Raster 5 mm, 20 mm hoch (22 mm Platz im Gehäuse). Polung beachten!"},
    {"name": "Raspberry Pi USB-C-Netzteil 5,1 V / 3 A", "qty": 1, "shop": "berrybase",
     "url": "https://www.berrybase.de/offizielles-raspberry-pi-usb-c-netzteil-5-1v-3-0a-eu-weiss",
     "note": "Stromversorgung fürs Herz. Weglassen, wenn du schon ein USB-C-Netzteil mit 3 A hast."},
    {"name": "Anycubic PLA+ Filament, Rot, 1 kg, 1,75 mm", "qty": 1, "shop": "amazon",
     "url": "https://www.amazon.de/s?k=Anycubic+PLA%2B+Filament+1kg+rot",
     "ref": ("Anycubic-Shop", "https://de.anycubic.com/products/pla-plus-filament.js", "Rot / 1KG"),
     "ref_eur": 18.99, "note": "Für Gehäuse, Gitter, Diffusor, Ständer: 210 g (1 Rolle reicht)."},
    {"name": "Blechschrauben-Sortiment (2,9 × 9,5 mm)", "qty": 1, "shop": "amazon",
     "url": "https://www.amazon.de/s?k=Blechschrauben+Sortiment+2%2C9+x+9%2C5",
     "ref": None, "ref_eur": 6.00,
     "note": "Du brauchst 3 Stück (Platine in die Abstandshalter). Alternativ M3 × 8 mm."},
]

# JLCPCB (Leiterplatte + Bestückung)
JOINTS = {"LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm": 4, "C_0603_1608Metric": 2,
          "R_0603_1608Metric": 2, "C_0805_2012Metric": 2, "SOT-23-5": 5, "D_SMA": 2,
          "USB_C_Receptacle_HRO_TYPE-C-31-M-12": 16}
BASIC = {"C14663", "C15850", "C23186", "C23138"}
JLC = {"setup": 8.18, "stencil": 1.53, "per_joint": 0.0016, "extended": 3.07, "hand_solder": 3.58}
# Echtes JLCPCB-Angebot vom 12.10.2026 (in Euro, ohne Bestückung):
# Ingenieurgebühr 3,56 + Leiterplatte 10,68 + Produktionsdatei bestätigen 0,93 = 15,18 €
PCB_5PCS_EUR = 15.18
SHIPPING_EUR = 23.85           # DHL Express laut Angebot – günstigere Versandart möglich

# Filament (Anycubic Kobra 2 Neo, cad/slicer_kobra2neo.ini)
FILAMENT_G = {"Rückschale": 88.55, "Pixel-Gitter": 57.88, "Diffusor": 21.89,
              "Ständer": 40.88, "Tasterstößel": 0.65}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


def berrybase(url):
    h = fetch(url)
    price = re.search(r'"price"\s*:\s*"?([0-9]+(?:\.[0-9]+)?)', h)
    av = re.search(r'"availability"\s*:\s*"[^"]*?([A-Za-z]+)"', h)
    sku = re.search(r'"sku"\s*:\s*"([^"]+)"', h)
    avail = {"InStock": "lieferbar", "LimitedAvailability": "lieferbar",
             "SoldOut": "AUSVERKAUFT", "OutOfStock": "AUSVERKAUFT"}.get(av.group(1) if av else "", "?")
    return float(price.group(1)), avail, sku.group(1) if sku else ""


def shopify_ref(js_url, variant):
    d = json.loads(fetch(js_url))
    for v in d["variants"]:
        if variant is None or v["title"] == variant:
            return v["price"] / 100, v["available"]
    raise ValueError("Variante nicht gefunden")


def lcsc_price(code, qty):
    d = json.loads(fetch(f"https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={code}"))["result"]
    ladder = sorted(d["productPriceList"], key=lambda p: p["ladder"])
    q = max(qty, ladder[0]["ladder"])
    price = ladder[0]["usdPrice"]
    for p in ladder:
        if q >= p["ladder"]:
            price = p["usdPrice"]
    return price


def de(v, d=2):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boards", type=int, default=2)
    n = max(2, ap.parse_args().boards)
    fx = json.loads(fetch("https://open.er-api.com/v6/latest/USD"))
    usd_eur = fx["rates"]["EUR"]
    eur_usd = 1 / usd_eur
    now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    E = lambda v: de(v) + " €"                       # noqa: E731
    U = lambda v, d=2: de(v, d) + " $"               # noqa: E731

    # --- selbst kaufen -----------------------------------------------------
    rows = []
    for it in ITEMS:
        if it["shop"] == "berrybase":
            price, avail, sku = berrybase(it["url"])
            src = f"BerryBase {sku}, live"
        else:
            price, avail, src = it["ref_eur"], "auf Amazon prüfen", "Richtwert (Schätzung)"
            if it["ref"]:
                try:
                    p, ok = shopify_ref(it["ref"][1], it["ref"][2])
                    price, src = p, f"Referenz {it['ref'][0]}, live"
                except Exception:
                    src = f"Referenz {it['ref'][0]} (Stand Okt. 2026)"
        rows.append((it, price, avail, src))
    self_eur = sum(it["qty"] * p for it, p, _, _ in rows)

    # --- JLCPCB --------------------------------------------------------------
    parts, parts_usd, joints, ext = [], 0.0, 0, 0
    with open(BOM) as f:
        for r in csv.DictReader(f):
            code, refs = r["LCSC Part #"], r["Designator"].split(",")
            qty = len(refs) * n
            u = lcsc_price(code, qty)
            parts_usd += u * qty
            joints += JOINTS[r["Footprint"]] * len(refs) * n
            ext += code not in BASIC
            parts.append((r["Comment"], code, qty, u))
    assy_usd = (JLC["setup"] + JLC["stencil"] + joints * JLC["per_joint"]
                + ext * JLC["extended"] + JLC["hand_solder"])
    PCB_5PCS_USD_ESTIMATE = PCB_5PCS_EUR * eur_usd    # Name bleibt, Wert jetzt echt
    SHIPPING_USD_ESTIMATE = SHIPPING_EUR * eur_usd
    jlc_usd = PCB_5PCS_USD_ESTIMATE + parts_usd + assy_usd + SHIPPING_USD_ESTIMATE
    total_eur = jlc_usd * usd_eur + self_eur
    fil_g = sum(FILAMENT_G.values())

    os.makedirs(OUTDIR, exist_ok=True)

    # --- links.md ------------------------------------------------------------
    L = ["# Einkaufsliste – Links (Deutschland)", "",
         f"Stand: {now}. Nur **BerryBase** und **Amazon (Versand durch Amazon)**, dazu JLCPCB für die Platine.", "",
         "## 1. Platine (fertig bestückt)", "",
         "| Was | Wo | Hinweis |", "|---|---|---|",
         "| Leiterplatte + Bestückung | [JLCPCB Online-Angebot](https://jlcpcb.com/quote) | "
         "`hardware/production/heart_gerber.zip` hochladen, dann BOM + CPL (siehe README) |", "",
         "## 2. BerryBase (alles in einer Bestellung)", "",
         "| Teil | Menge | Link | Verfügbar | Hinweis |", "|---|---|---|---|---|"]
    for it, p, av, src in rows:
        if it["shop"] == "berrybase":
            L.append(f"| {it['name']} | {it['qty']} | [BerryBase]({it['url']}) | {av} | {it['note']} |")
    L += ["", "## 3. Amazon (nur Angebote mit „Versand durch Amazon“)", "",
          "| Teil | Menge | Link | Hinweis |", "|---|---|---|---|"]
    for it, p, av, src in rows:
        if it["shop"] == "amazon":
            L.append(f"| {it['name']} | {it['qty']} | [Amazon-Suche]({it['url']}) | {it['note']} |")
    L += ["",
          "**So findest du „Versand durch Amazon“:** In der Amazon-Suche links den Filter **Prime** setzen. "
          "Auf der Produktseite rechts im Kaufkasten muss bei **Versand** „Amazon“ stehen "
          "(Verkäufer darf ein anderer sein). Steht dort ein anderer Versender: nicht nehmen.", "",
          "Die Amazon-Links sind Suchlinks, weil Amazon automatische Abfragen blockt. Ich konnte dort "
          "Preise und Versandart nicht selbst prüfen. Schau vor dem Kauf genau hin:", "",
          "- **XIAO:** Es muss wirklich „Seeed Studio XIAO ESP32C3“ sein (21 × 17,8 mm). "
          "Der XIAO ESP32-S3 passt auch (gleiche Pins, Firmware unterstützt ihn).",
          "- **PLA+:** Marke Anycubic, 1,75 mm, 1 kg, Farbe Rot.", ""]
    with open(os.path.join(OUTDIR, "links.md"), "w") as f:
        f.write("\n".join(L) + "\n")

    # --- price.md ------------------------------------------------------------
    P = ["# Preise – LED-Herz (Euro und Dollar)", "",
         f"Stand: **{now}** · Kurs: 1 $ = {de(usd_eur, 4)} € · 1 € = {de(eur_usd, 4)} $ "
         f"(open.er-api.com, {fx.get('time_last_update_utc', '')})", "",
         f"Neu berechnen: `python3 tools/einkauf.py --boards {n}`. **Live** = gerade vom Shop abgefragt, "
         "**Schätzung** = bitte selbst prüfen.", "",
         "## Zusammenfassung", "",
         "| Posten | Euro | Dollar |", "|---|---|---|",
         f"| JLCPCB: 5 Platinen, davon {n} bestückt, inkl. Versand | {E(jlc_usd * usd_eur)} | {U(jlc_usd)} |",
         f"| Selbst kaufen (BerryBase + Amazon) | {E(self_eur)} | {U(self_eur * eur_usd)} |",
         f"| **Gesamt** | **{E(total_eur)}** | **{U(total_eur * eur_usd)}** |", "",
         "Versandkosten bei BerryBase und Amazon sind nicht eingerechnet (hängen vom Warenkorb ab).", "",
         "## Selbst kaufen", "",
         "| Teil | Shop | Menge | Stück € | Stück $ | Summe € | Summe $ | Preisquelle |",
         "|---|---|---|---|---|---|---|---|"]
    for it, p, av, src in rows:
        shop = "BerryBase" if it["shop"] == "berrybase" else "Amazon"
        P.append(f"| {it['name']} | {shop} | {it['qty']} | {E(p)} | {U(p * eur_usd)} | "
                 f"{E(it['qty'] * p)} | {U(it['qty'] * p * eur_usd)} | {src} |")
    P += [f"| **Summe** | | | | | **{E(self_eur)}** | **{U(self_eur * eur_usd)}** | |", "",
          "## JLCPCB", "",
          "| Posten | Dollar | Euro | Quelle |", "|---|---|---|---|"]
    P.append(f"| 5 × Leiterplatte 2 Lagen, 162 × 153 mm | {U(PCB_5PCS_USD_ESTIMATE)} | "
             f"{E(PCB_5PCS_USD_ESTIMATE * usd_eur)} | JLCPCB-Angebot 12.10.2026 (inkl. Ingenieurgebühr + Dateibestätigung) |")
    for c, code, qty, u in parts:
        P.append(f"| {c} ({code}) × {qty} | {U(u * qty)} | {E(u * qty * usd_eur)} | LCSC live, {U(u, 4)}/Stück |")
    P += [f"| Bestückung: Einrichtung | {U(JLC['setup'])} | {E(JLC['setup'] * usd_eur)} | JLCPCB-Preisliste |",
          f"| Bestückung: Schablone | {U(JLC['stencil'])} | {E(JLC['stencil'] * usd_eur)} | JLCPCB-Preisliste |",
          f"| Bestückung: {joints} Lötstellen | {U(joints * JLC['per_joint'])} | "
          f"{E(joints * JLC['per_joint'] * usd_eur)} | JLCPCB-Preisliste |",
          f"| Bestückung: {ext} Extended-Teile | {U(ext * JLC['extended'])} | "
          f"{E(ext * JLC['extended'] * usd_eur)} | JLCPCB-Preisliste |",
          f"| Bestückung: ggf. Handlöten USB-C | {U(JLC['hand_solder'])} | "
          f"{E(JLC['hand_solder'] * usd_eur)} | JLCPCB-Preisliste |",
          f"| Versand nach Deutschland | {U(SHIPPING_USD_ESTIMATE)} | "
          f"{E(SHIPPING_USD_ESTIMATE * usd_eur)} | JLCPCB-Angebot, DHL Express (billigere Versandart wählbar) |",
          f"| **Summe JLCPCB** | **{U(jlc_usd)}** | **{E(jlc_usd * usd_eur)}** | |", "",
          "Platinenfläche ca. 247 cm², also kein Großformat-Aufschlag (erst ab 650 cm²). "
          "Leiterplatte und Versand: echtes JLCPCB-Angebot. Bauteile und Bestückung: berechnet aus "
          "LCSC-Preisen und der JLCPCB-Preisliste – den genauen Betrag zeigt JLCPCB, sobald die "
          "Leiterplattenmontage eingeschaltet ist. Gutscheine von JLCPCB sind nicht abgezogen.", "",
          "## Filament (Anycubic Kobra 2 Neo)", "",
          "| Teil | Gramm |", "|---|---|"]
    P += [f"| {k} | {v:.0f} g |" for k, v in FILAMENT_G.items()]
    P += [f"| **Summe** | **{fil_g:.0f} g** → {math.ceil(fil_g * 1.15 / 1000)} Rolle à 1 kg reicht |", ""]
    with open(os.path.join(OUTDIR, "price.md"), "w") as f:
        f.write("\n".join(P) + "\n")

    print(f"OK: {OUTDIR}/links.md, price.md")
    print(f"  JLCPCB {E(jlc_usd * usd_eur)} / {U(jlc_usd)}, selbst {E(self_eur)}, gesamt {E(total_eur)}")
    for it, p, av, src in rows:
        print(f"  {it['name'][:40]:40s} {E(p):>9}  {av:18s} {src}")


if __name__ == "__main__":
    main()
