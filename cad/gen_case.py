#!/usr/bin/env python3
"""
Gehäuse + Ständer für das LED-Herz (CadQuery).

    pip install cadquery
    python3 cad/gen_case.py

Erzeugt in cad/out/:
    *.step  -> in Fusion 360 öffnen (Datei > Öffnen > Von meinem Computer)
    *.stl   -> zum 3D-Druck (z.B. bei einem Druckdienst bestellen)
    heart_case_assembly.step -> alles zusammengebaut, inkl. Platine

Koordinaten: x nach rechts, y nach oben, z nach vorne (zum Betrachter).
Die Platine liegt so wie in KiCad (Platinen-y zeigt nach unten -> hier -y).
"""
import math
import os

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

# --------------------------------------------------------------------------
# Maße (mm) – hier anpassen
# --------------------------------------------------------------------------
CLEAR = 0.5          # Luft zwischen Platine und Gehäusewand
WALL = 2.0           # Wandstärke
FLOOR = 2.5          # Rückwand
BACK_DEPTH = 22.0    # Platz hinter der Platine (XIAO auf Buchsenleisten, Elko bis 20 mm hoch)
PCB_T = 1.6
GAP = 4.0            # Luft zwischen Platine und Gitter (USB-C-Buchse ist 3,2 mm hoch)
GRID_T = 10.0        # Tiefe des Pixel-Gitters
DIFF_T = 1.0         # Diffusor-Platte
CELL = 14.0          # Zellgröße im Gitter (LED-Raster 16 mm -> 2 mm Stege)

Z_PCB_BOT = FLOOR + BACK_DEPTH
Z_PCB_TOP = Z_PCB_BOT + PCB_T
Z_GRID = Z_PCB_TOP + GAP
Z_DIFF = Z_GRID + GRID_T
Z_TOP = Z_DIFF + DIFF_T

# Aus hardware/gen_pcb.py übernommen (Platinenkoordinaten, y nach unten)
MASK = [".XX...XX.", "XXXX.XXXX", "XXXXXXXXX", "XXXXXXXXX",
        ".XXXXXXX.", "..XXXXX..", "...XXX...", "....X...."]
PITCH = 16.0
LOBE_X, LOBE_Y, TIP_Y = 30.0, -32.0, 70.0
HOLES = [(-40, -47), (40, -47), (0, -48)]
BUTTON = (28.0, 0.0)
XIAO = (0.0, 23.62)         # Mitte der Buchsenleisten
ELKO = (24.5, 16.0)         # Mitte des 1000 µF Elkos (Rückseite)
USB_FLANK = (-47.0, 23.0)   # Punkt auf der Platinenkante, an dem die USB-C-Buchse sitzt


def P(x, y):
    """Platinenkoordinate -> CAD (y umdrehen)"""
    return (x, -y)


def heart_outline(n=120):
    r = (TIP_Y - LOBE_X - LOBE_Y) / math.sqrt(2)
    notch = math.atan2(math.sqrt(r ** 2 - LOBE_X ** 2), -LOBE_X)
    right = []
    for i in range(n + 1):
        a = math.radians(-45) + (notch - math.radians(-45)) * i / n
        right.append((LOBE_X + r * math.cos(a), LOBE_Y - r * math.sin(a)))
    left = [(-x, y) for x, y in reversed(right)]
    pts = [(0.0, TIP_Y)] + right + left[1:]
    return [P(x, y) for x, y in pts]


OUTLINE = heart_outline()


def heart_sketch(z0=0.0):
    """Herzumriss aus echten Kreisbögen + 2 Geraden (glatte Flächen in Fusion 360)"""
    r = (TIP_Y - LOBE_X - LOBE_Y) / math.sqrt(2)
    notch = math.atan2(math.sqrt(r ** 2 - LOBE_X ** 2), -LOBE_X)
    cx, cy = LOBE_X, -LOBE_Y                    # rechter Bogenmittelpunkt in CAD-Koordinaten

    def pt(a, sign=1):
        return (sign * (cx + r * math.cos(a)), cy + r * math.sin(a))
    a0 = math.radians(-45)
    mid = (a0 + notch) / 2
    return (cq.Workplane("XY").workplane(offset=z0)
            .moveTo(0, -TIP_Y).lineTo(*pt(a0))
            .threePointArc(pt(mid), pt(notch))
            .threePointArc(pt(mid, -1), pt(a0, -1))
            .close())


def heart(offset=0.0, z0=0.0, h=1.0):
    """Herzförmiges Prisma, um 'offset' vergrößert (negativ = kleiner)"""
    wp = heart_sketch(z0)
    if offset:
        wp = wp.offset2D(offset, "arc")
    return wp.extrude(h)


def leds():
    for r, row in enumerate(MASK):
        for c, ch in enumerate(row):
            if ch == "X":
                yield P((c - 4) * PITCH, (r - 3.5) * PITCH)


# --------------------------------------------------------------------------
# 1) Rückschale
# --------------------------------------------------------------------------
def make_shell():
    s = heart(CLEAR + WALL, 0, Z_TOP)
    s = s.cut(heart(CLEAR, FLOOR, Z_TOP))
    # Auflage-Kante für das Gitter (1,5 mm breit, ragt 1 mm über den Platinenrand)
    ledge = heart(CLEAR, Z_GRID - 2.0, 2.0).cut(heart(-1.0, Z_GRID - 2.0, 2.0))
    s = s.union(ledge)
    # Abstandshalter für die Platine, Loch für M3-Schraube (selbstschneidend)
    for hx, hy in HOLES:
        x, y = P(hx, hy)
        post = (cq.Workplane("XY").workplane(offset=FLOOR).center(x, y)
                .circle(3.5).extrude(BACK_DEPTH))
        s = s.union(post)
        s = s.cut(cq.Workplane("XY").workplane(offset=Z_PCB_BOT - 10).center(x, y)
                  .circle(1.25).extrude(10))
    # Öffnung für die USB-C-Buchse auf der linken Flanke, oben offen
    fx, fy = P(*USB_FLANK)
    nx, ny = -1 / math.sqrt(2), -1 / math.sqrt(2)          # Außennormale (CAD)
    cx, cy = fx + nx * (CLEAR + WALL / 2), fy + ny * (CLEAR + WALL / 2)
    slot = (cq.Workplane("XY").workplane(offset=Z_PCB_BOT - 2.5)
            .center(cx, cy).transformed(rotate=(0, 0, -45))
            .rect(13.0, 9.0).extrude(Z_TOP))
    s = s.cut(slot)
    # Fenster hinter dem XIAO: USB-Kabel zum Flashen einstecken
    xx, xy = P(*XIAO)
    s = s.cut(cq.Workplane("XY").center(xx - 15.0, xy).rect(36.0, 22.0).extrude(FLOOR))
    # Loch für den Tasterstößel
    bx, by = P(*BUTTON)
    s = s.cut(cq.Workplane("XY").center(bx, by).circle(2.9).extrude(FLOOR))
    # Zwei Schlüssellöcher zum Aufhängen (Schraubenkopf bis 7,5 mm)
    for kx in (-45.0, 45.0):
        x, y = P(kx, -30.0)
        s = s.cut(cq.Workplane("XY").center(x, y).circle(3.9).extrude(FLOOR))
        s = s.cut(cq.Workplane("XY").center(x, y + 4.0).rect(4.2, 8.0).extrude(FLOOR))
    return s


# --------------------------------------------------------------------------
# 2) Pixel-Gitter: jede LED bekommt ihre eigene quadratische Zelle
# --------------------------------------------------------------------------
def make_grid():
    """Durchgehendes 16-mm-Raster (2 mm Stege) mit 2 mm Rand – spart Material."""
    g = heart(CLEAR - 0.3, Z_GRID, GRID_T)
    pts = [P((c - 4) * PITCH, (r - 3.5) * PITCH) for r in range(-1, 9) for c in range(-1, 10)]
    cells = cq.Workplane("XY").workplane(offset=Z_GRID).pushPoints(pts).rect(CELL, CELL)
    g = g.cut(cells.extrude(GRID_T))
    rim = heart(CLEAR - 0.3, Z_GRID, GRID_T).cut(heart(CLEAR - 2.3, Z_GRID, GRID_T))
    return g.union(rim)


# --------------------------------------------------------------------------
# 3) Diffusor (optional, weiß/transluzent) – oder einfach Transparentpapier
# --------------------------------------------------------------------------
def make_diffuser():
    return heart(CLEAR - 0.3, Z_DIFF, DIFF_T)


# --------------------------------------------------------------------------
# 4) Tasterstößel: steckt im Loch der Rückwand und drückt auf den Taster
# --------------------------------------------------------------------------
BUTTON_H = 4.9   # Höhe Taster ab Platine (6x6 mm THT, meist 4,3–5 mm) – ggf. anpassen


def make_plunger():
    bx, by = P(*BUTTON)
    tip = Z_PCB_BOT - BUTTON_H
    p = cq.Workplane("XY").workplane(offset=-1.0).center(bx, by).circle(2.6).extrude(tip + 1.0)
    collar = cq.Workplane("XY").workplane(offset=tip - 2.5).center(bx, by).circle(4.0).extrude(1.5)
    return p.union(collar)


# --------------------------------------------------------------------------
# 5) Ständer: 90°-V-Tasche für die Herzspitze, 10° nach hinten geneigt
# --------------------------------------------------------------------------
STAND_TILT = 10.0


def make_stand():
    depth = Z_TOP + 1.0                     # Tasche etwas tiefer als das Gehäuse dick ist
    w, d, h = 90.0, depth + 18.0, 30.0
    base = cq.Workplane("XY").box(w, d, h, centered=(True, True, False))
    # V-Prisma (Spitze unten) in der x-z-Ebene des Herzens, extrudiert in Tiefe
    v = 26.0
    tri = (cq.Workplane("XZ").polyline([(0, 0), (v + 6, v + 6), (-(v + 6), v + 6)]).close()
           .extrude(-depth / 2, both=True))
    tri = tri.rotate((0, 0, 0), (1, 0, 0), -STAND_TILT).translate((0, -2.0, h - v))
    base = base.cut(tri)
    # vordere Wand niedriger, damit die unterste LED frei bleibt
    base = base.cut(cq.Workplane("XY").workplane(offset=h - v + 9.0)
                    .center(0, -d / 2 + 4.5).rect(w, 9.0 + 2.0).extrude(30))
    return base.edges("|Z").fillet(4.0)


def stand_pose(obj):
    """Gehäuse in den Ständer stellen (für das Zusammenbau-Modell)"""
    tip_y = P(0, TIP_Y)[1] - (CLEAR + WALL) * math.sqrt(2)  # Spitze der Außenkontur
    o = obj.translate((0, -tip_y, 0))                        # Spitze auf y = 0
    o = o.rotate((0, 0, 0), (1, 0, 0), 90)                   # aufstellen: Herz-y -> z
    o = o.translate((0, Z_TOP / 2, 0))                       # Gehäusemitte über Taschenmitte
    o = o.rotate((0, 0, 0), (1, 0, 0), -STAND_TILT).translate((0, -2.0, 30.0 - 26.0))
    return o


# --------------------------------------------------------------------------
# Platzhalter für die Bauteile (nur zur Kollisionsprüfung)
# --------------------------------------------------------------------------
def box_at(x, y, sx, sy, z0, h):
    cx, cy = P(x, y)
    return cq.Workplane("XY").workplane(offset=z0).center(cx, cy).rect(sx, sy).extrude(h)


def make_dummies():
    pcb = heart(0, Z_PCB_BOT, PCB_T)
    xiao = box_at(XIAO[0], XIAO[1], 21.0, 17.8, Z_PCB_BOT - 12.5, 12.5)       # Leisten + Modul
    elko = (cq.Workplane("XY").workplane(offset=Z_PCB_BOT - 20.0)
            .center(*P(*ELKO)).circle(5.0).extrude(20.0))
    button = box_at(BUTTON[0], BUTTON[1], 6.0, 6.0, Z_PCB_BOT - BUTTON_H, BUTTON_H)
    fx, fy = P(*USB_FLANK)
    usb = (cq.Workplane("XY").workplane(offset=Z_PCB_TOP)
           .center(fx + 1.3, fy + 1.3).transformed(rotate=(0, 0, -45))
           .rect(8.94, 7.35).extrude(3.2))
    leds_ = cq.Workplane("XY").workplane(offset=Z_PCB_TOP).pushPoints(list(leds())).rect(5, 5).extrude(1.6)
    return {"pcb": pcb, "xiao": xiao, "elko": elko, "button": button, "usb": usb, "leds": leds_}


def main():
    parts = {
        "heart_case_shell": make_shell(),
        "heart_case_grid": make_grid(),
        "heart_case_diffuser": make_diffuser(),
        "heart_case_button_plunger": make_plunger(),
        "heart_stand": make_stand(),
    }
    for name, wp in parts.items():
        cq.exporters.export(wp, os.path.join(OUT, name + ".step"))
        cq.exporters.export(wp, os.path.join(OUT, name + ".stl"), tolerance=0.05, angularTolerance=0.2)
        bb = wp.val().BoundingBox()
        print(f"{name:28s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:5.1f} mm  "
              f"Volumen {wp.val().Volume() / 1000:6.1f} cm³")

    dummies = make_dummies()

    # Kollisionsprüfung: Bauteile dürfen keine Gehäuseteile schneiden
    print("\nKollisionsprüfung:")
    bad = 0
    for pname in ("heart_case_shell", "heart_case_grid", "heart_case_diffuser",
                  "heart_case_button_plunger"):
        for dname, d in dummies.items():
            if pname == "heart_case_button_plunger" and dname == "button":
                continue  # der Stößel soll den Taster berühren
            vol = parts[pname].intersect(d).val().Volume() if parts[pname].intersect(d).vals() else 0
            if vol > 0.01:
                print(f"  KOLLISION {pname} <-> {dname}: {vol:.2f} mm³")
                bad += 1
    print("  OK, nichts kollidiert" if not bad else f"  {bad} Kollisionen!")

    # Zusammenbau (Gehäuse im Ständer, Platine mit Platzhaltern)
    asm = cq.Assembly(name="LED-Herz")
    colors = {"heart_case_shell": (0.85, 0.15, 0.3), "heart_case_grid": (0.15, 0.15, 0.15),
              "heart_case_diffuser": (1, 1, 1, 0.5), "heart_case_button_plunger": (0.9, 0.9, 0.9),
              "heart_stand": (0.3, 0.3, 0.35)}
    for name, wp in parts.items():
        obj = wp if name == "heart_stand" else stand_pose(wp)
        asm.add(obj, name=name, color=cq.Color(*colors[name]))
    pcb_step = os.path.join(OUT, "heart_pcb.step")  # aus KiCad: siehe README
    if os.path.exists(pcb_step):
        dummies["pcb"] = cq.importers.importStep(pcb_step).translate((0, 0, Z_PCB_BOT))
    for name, wp in dummies.items():
        col = {"pcb": (0.1, 0.45, 0.2), "leds": (1, 1, 0.9)}.get(name, (0.6, 0.6, 0.6))
        asm.add(stand_pose(wp), name="platzhalter_" + name, color=cq.Color(*col))
    asm.export(os.path.join(OUT, "heart_case_assembly.step"))
    print(f"\nFertig: {OUT}")
    return bad


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
