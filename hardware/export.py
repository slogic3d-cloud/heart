#!/usr/bin/env python3
"""
Erzeugt alle Dateien für die JLCPCB-Bestellung:

    python3 hardware/export.py

hardware/production/
    heart_gerber.zip   -> bei JLCPCB als "Gerber" hochladen
    heart_bom.csv      -> "BOM" (Stückliste mit LCSC-Nummern)
    heart_cpl.csv      -> "CPL" (Bestückungspositionen)
"""
import csv
import os
import shutil
import subprocess
import zipfile

os.environ.setdefault("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
import pcbnew  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "heart.kicad_pcb")
OUT = os.path.join(HERE, "production")
GERB = os.path.join(OUT, "gerber")

# Wert/Footprint -> (LCSC-Nummer, Bauteilbeschreibung). Alle per LCSC geprüft.
LCSC = {
    "WS2812B": ("C114586", "WS2812B-B/W 5050 RGB LED"),
    "100nF": ("C14663", "100nF 50V X7R 0603"),
    "10uF": ("C15850", "10uF 25V X5R 0805"),
    "5k1": ("C23186", "5.1k 1% 0603"),
    "330R": ("C23138", "330R 1% 0603"),
    "74AHCT1G125": ("C7484", "SN74AHCT1G125DBVR"),
    "SS34": ("C408258", "SS34 Schottky 40V 3A SMA"),
    "USB-C Power": ("C165948", "HRO TYPE-C-31-M-12"),
}


def run(*args):
    print("$", " ".join(args))
    subprocess.run(args, check=True)


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(GERB)

    layers = "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
    run("kicad-cli", "pcb", "export", "gerbers", "--layers", layers,
        "--subtract-soldermask", "-o", GERB + "/", PCB)
    run("kicad-cli", "pcb", "export", "drill", "--format", "excellon",
        "--excellon-separate-th", "-o", GERB + "/", PCB)
    with zipfile.ZipFile(os.path.join(OUT, "heart_gerber.zip"), "w",
                         zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(GERB)):
            z.write(os.path.join(GERB, f), f)

    board = pcbnew.LoadBoard(PCB)
    bom = {}
    cpl = []
    for fp in board.GetFootprints():
        ref, val = fp.GetReference(), fp.GetValue()
        if val not in LCSC or fp.IsFlipped():
            continue  # THT-Teile (Taster, Elko, Buchsenleisten) lötest du selbst
        pos = fp.GetPosition()
        cpl.append([ref, f"{pcbnew.ToMM(pos.x):.3f}mm", f"{-pcbnew.ToMM(pos.y):.3f}mm",
                    "Top", f"{fp.GetOrientationDegrees() % 360:.1f}"])
        key = (val, fp.GetFPID().GetLibItemName().wx_str())
        bom.setdefault(key, []).append(ref)

    def refkey(r):
        return (r.rstrip("0123456789"), int("".join(c for c in r if c.isdigit()) or 0))

    with open(os.path.join(OUT, "heart_bom.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (val, fpname), refs in sorted(bom.items()):
            refs.sort(key=refkey)
            w.writerow([LCSC[val][1], ",".join(refs), fpname, LCSC[val][0]])
    with open(os.path.join(OUT, "heart_cpl.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for row in sorted(cpl, key=lambda r: refkey(r[0])):
            w.writerow(row)

    n = sum(len(v) for v in bom.values())
    print(f"\nFertig: {OUT}\n  {n} SMD-Teile in {len(bom)} BOM-Zeilen")


if __name__ == "__main__":
    main()
