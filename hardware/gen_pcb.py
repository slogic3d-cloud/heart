#!/usr/bin/env python3
"""
Erzeugt die komplette Herz-Platine (KiCad 7+) per Skript.

    python3 hardware/gen_pcb.py

Ergebnis: hardware/heart.kicad_pcb (+ .kicad_pro), danach mit
hardware/export.sh Gerber/BOM/CPL für JLCPCB erzeugen.

Alles in mm. Koordinaten relativ zur Herzmitte, y zeigt nach unten.
"""
import math
import os
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "heart.kicad_pcb")
FPLIB = "/usr/share/kicad/footprints"
if not os.path.isdir(FPLIB):
    FPLIB = os.environ.get("KICAD7_FOOTPRINT_DIR", FPLIB)

# --------------------------------------------------------------------------
# Herz-Matrix – MUSS mit firmware src/heart_map.h übereinstimmen
# --------------------------------------------------------------------------
MASK = [
    ".XX...XX.",
    "XXXX.XXXX",
    "XXXXXXXXX",
    "XXXXXXXXX",
    ".XXXXXXX.",
    "..XXXXX..",
    "...XXX...",
    "....X....",
]
ROWS, COLS = len(MASK), len(MASK[0])
PITCH = 16.0
ORIGIN = (150.0, 110.0)  # Platinenmitte auf dem KiCad-Blatt

TRACK = 0.25
POWER_TRACK = 0.6
VIA_D, VIA_DRILL = 0.6, 0.3


def mm(v):
    return pcbnew.FromMM(v)


def V(x, y):
    return pcbnew.VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))


def unV(p):
    return (pcbnew.ToMM(p.x) - ORIGIN[0], pcbnew.ToMM(p.y) - ORIGIN[1])


def led_xy(c, r):
    return ((c - (COLS - 1) / 2) * PITCH, (r - (ROWS - 1) / 2) * PITCH)


def chain_order():
    """Reihenfolge der LEDs entlang der Datenleitung.
    Start unten an der Spitze, dann Schlangenlinie nach oben.
    Gerade Zeilen (von unten gezählt) laufen links->rechts."""
    order = []
    for k, r in enumerate(range(ROWS - 1, -1, -1)):
        cols = [c for c in range(COLS) if MASK[r][c] == "X"]
        if k % 2:
            cols.reverse()
        order += [(c, r, k % 2 == 0) for c in cols]
    return order


# --------------------------------------------------------------------------
board = pcbnew.NewBoard(OUT)
ds = board.GetDesignSettings()
ds.SetCopperLayerCount(2)
ds.m_TrackMinWidth = mm(0.2)
ds.m_ViasMinSize = mm(0.5)
ds.m_MinThroughDrill = mm(0.3)
ds.m_CopperEdgeClearance = mm(0.4)
ns = ds.m_NetSettings
ns.m_DefaultNetClass.SetClearance(mm(0.2))
ns.m_DefaultNetClass.SetTrackWidth(mm(TRACK))
ns.m_DefaultNetClass.SetViaDiameter(mm(VIA_D))
ns.m_DefaultNetClass.SetViaDrill(mm(VIA_DRILL))

nets = {}


def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n
    return nets[name]


def load(lib, name):
    fp = pcbnew.FootprintLoad(os.path.join(FPLIB, lib + ".pretty"), name)
    assert fp is not None, (lib, name)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def place(fp, ref, value, x, y, rot=0, back=False):
    fp.SetReference(ref)
    fp.SetValue(value)
    board.Add(fp)
    fp.SetPosition(V(x, y))
    fp.SetOrientationDegrees(rot)
    if back:
        fp.Flip(fp.GetPosition(), False)
    if (ref[0] in "CD" and ref[1:].isdigit() and int(ref[1:]) <= 46) or ref in ("R2", "R3"):
        fp.Reference().SetVisible(False)  # 92 Bauteile – Beschriftung wäre nur Gewusel
    return fp


def setnets(fp, mapping):
    for pad in fp.Pads():
        n = mapping.get(pad.GetNumber())
        if n:
            pad.SetNet(net(n))


def padxy(fp, num):
    pads = [p for p in fp.Pads() if p.GetNumber() == num]
    assert pads, (fp.GetReference(), num)
    return unV(pads[0].GetPosition())


def track(netname, pts, layer=pcbnew.F_Cu, width=TRACK):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(x1, y1))
        t.SetEnd(V(x2, y2))
        t.SetWidth(mm(width))
        t.SetLayer(layer)
        t.SetNet(net(netname))
        board.Add(t)


def via(netname, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(V(x, y))
    v.SetWidth(mm(VIA_D))
    v.SetDrill(mm(VIA_DRILL))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(net(netname))
    board.Add(v)


def silk_text(txt, x, y, size=1.5, layer=pcbnew.F_SilkS, mirror=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetPosition(V(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    t.SetMirrored(mirror)
    board.Add(t)


# --------------------------------------------------------------------------
# Platinenumriss: zwei Kreisbögen (Herzbögen) + 45°-Flanken zur Spitze.
# Die unteren LED-Zeilen bilden eine 45°-Treppe – die Flanken laufen parallel.
# Die USB-C-Buchse sitzt auf der linken Flanke (Kabel hängt nach unten raus).
# --------------------------------------------------------------------------
LOBE_X, LOBE_Y = 30.0, -32.0   # Mittelpunkte der beiden Bögen (±LOBE_X)
TIP_Y = 70.0                   # Spitze unten (Flanken: |x| + y = TIP_Y)
LOBE_R = (TIP_Y - LOBE_X - LOBE_Y) / math.sqrt(2)  # Bogen tangential an die Flanke


def heart_outline(n=180):
    # rechter Bogen: vom Tangentenpunkt (unten rechts, -45°) gegen den
    # Uhrzeigersinn bis zur Kerbe in der Mitte
    notch_a = math.atan2(math.sqrt(LOBE_R ** 2 - LOBE_X ** 2), -LOBE_X)  # Kerbe
    a0, a1 = math.radians(-45), notch_a
    right = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        right.append((LOBE_X + LOBE_R * math.cos(a), LOBE_Y - LOBE_R * math.sin(a)))
    left = [(-x, y) for x, y in reversed(right)]
    return [(0.0, TIP_Y)] + right + left[1:]


outline = heart_outline()


for (x1, y1), (x2, y2) in zip(outline, outline[1:] + outline[:1]):
    seg = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    seg.SetLayer(pcbnew.Edge_Cuts)
    seg.SetWidth(mm(0.1))
    seg.SetStart(V(x1, y1))
    seg.SetEnd(V(x2, y2))
    board.Add(seg)

# --------------------------------------------------------------------------
# LEDs + Abblockkondensatoren + Datenkette
# --------------------------------------------------------------------------
order = chain_order()
leds = []
for i, (c, r, ltr) in enumerate(order):
    x, y = led_xy(c, r)
    rot = 180 if ltr else 0  # Footprint: DIN rechts oben, DOUT links unten
    n = i + 1
    d = place(load("LED_SMD", "LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm"),
              f"D{n}", "WS2812B", x, y, rot)
    din = "DATA_5V" if i == 0 else f"LED{n - 1}_DOUT"
    dout = f"LED{n}_DOUT" if i < len(order) - 1 else None
    setnets(d, {"1": "+5V", "3": "GND", "4": din, **({"2": dout} if dout else {})})
    # 100 nF unter (bzw. bei 180° über) der LED, GND-Seite neben VSS
    s = -1 if ltr else 1
    cap = place(load("Capacitor_SMD", "C_0603_1608Metric"), f"C{n}", "100nF",
                x, y + s * 4.6, rot)
    setnets(cap, {"1": "+5V", "2": "GND"})
    vx, vy = x + s * 2.45, y + s * 3.6
    via("GND", vx, vy)
    track("GND", [padxy(d, "3"), (vx, vy)], width=0.5)
    track("GND", [padxy(cap, "2"), (padxy(cap, "2")[0], vy), (vx, vy)], width=0.4)
    leds.append((d, x, y, ltr))

# Datenleitungen zwischen den LEDs
for i in range(len(leds) - 1):
    d, x, y, ltr = leds[i]
    d2, x2, y2, ltr2 = leds[i + 1]
    a = padxy(d, "2")
    b = padxy(d2, "4")
    nn = f"LED{i + 1}_DOUT"
    if y2 == y:  # gleiche Zeile: raus, 45° Schräge, rein
        s = 1 if ltr else -1
        track(nn, [a, (a[0] + s * 2.5, a[1]), (a[0] + s * 5.8, b[1]), b])
    elif abs(abs(b[0] - a[0]) - abs(b[1] - a[1])) < 0.01:
        # Zeilenwechsel auf der 45°-Treppe: schräg hoch, mittig zwischen den Pads
        sx = 1 if b[0] > a[0] else -1
        if ltr == (sx > 0):
            track(nn, [a, (a[0] + sx * 0.85, a[1]), (b[0] + sx * 0.85, b[1]), b])
        else:  # erst senkrecht am eigenen Kondensator vorbei
            up = a[1] - 4.85
            track(nn, [a, (a[0], up), (a[0] + sx * (up - b[1]), b[1]), b])
    else:  # Zeilenwechsel bei senkrechter Kante: 2 mm nach außen ausweichen
        s = 1 if ltr else -1
        xo = a[0] + s * 2.0
        track(nn, [a, (xo, a[1] - 2.0), (xo, b[1] + 2.0), b])

# --------------------------------------------------------------------------
# Seeed XIAO ESP32-C3 (Rückseite, auf 2x 1x7 Buchsenleisten)
# --------------------------------------------------------------------------
XIAO_PINS = {  # lokale Koordinaten von OBEN auf das Modul gesehen, USB oben
    "1": ("D0", -7.62, -7.62), "2": ("D1", -7.62, -5.08), "3": ("D2", -7.62, -2.54),
    "4": ("D3", -7.62, 0.0), "5": ("D4", -7.62, 2.54), "6": ("D5", -7.62, 5.08),
    "7": ("D6", -7.62, 7.62), "8": ("D7", 7.62, 7.62), "9": ("D8", 7.62, 5.08),
    "10": ("D9", 7.62, 2.54), "11": ("D10", 7.62, 0.0), "12": ("3V3", 7.62, -2.54),
    "13": ("GND", 7.62, -5.08), "14": ("5V", 7.62, -7.62),
}


def make_xiao():
    fp = pcbnew.FOOTPRINT(board)
    fp.SetFPID(pcbnew.LIB_ID("heart", "Seeed_XIAO_Socket"))
    for num, (name, x, y) in XIAO_PINS.items():
        p = pcbnew.PAD(fp)
        p.SetNumber(num)
        p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        p.SetShape(pcbnew.PAD_SHAPE_RECT if num == "1" else pcbnew.PAD_SHAPE_CIRCLE)
        p.SetSize(pcbnew.VECTOR2I(mm(1.7), mm(1.7)))
        p.SetDrillSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        p.SetLayerSet(pcbnew.PAD.PTHMask())
        p.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        p.SetPos0(pcbnew.VECTOR2I(mm(x), mm(y)))
        fp.Add(p)
    # Modulumriss 17.8 x 21 mm, USB-C ragt oben 1.5 mm raus
    for (x1, y1, x2, y2) in [(-8.9, -10.5, 8.9, -10.5), (8.9, -10.5, 8.9, 10.5),
                             (8.9, 10.5, -8.9, 10.5), (-8.9, 10.5, -8.9, -10.5),
                             (-4.5, -10.5, -4.5, -12), (4.5, -10.5, 4.5, -12),
                             (-4.5, -12, 4.5, -12)]:
        for layer, w in ((pcbnew.F_SilkS, 0.15), (pcbnew.F_Fab, 0.1)):
            ln = pcbnew.FP_SHAPE(fp, pcbnew.SHAPE_T_SEGMENT)
            ln.SetLayer(layer)
            ln.SetWidth(mm(w))
            ln.SetStart0(pcbnew.VECTOR2I(mm(x1), mm(y1)))
            ln.SetEnd0(pcbnew.VECTOR2I(mm(x2), mm(y2)))
            fp.Add(ln)
    cy = pcbnew.FP_SHAPE(fp, pcbnew.SHAPE_T_RECT)
    cy.SetLayer(pcbnew.F_CrtYd)
    cy.SetWidth(mm(0.05))
    cy.SetStart0(pcbnew.VECTOR2I(mm(-9.2), mm(-12.3)))
    cy.SetEnd0(pcbnew.VECTOR2I(mm(9.2), mm(10.8)))
    fp.Add(cy)
    return fp


LIBDIR = os.path.join(HERE, "heart.pretty")
if not os.path.isdir(LIBDIR):
    pcbnew.FootprintLibCreate(LIBDIR)
pcbnew.FootprintSave(LIBDIR, make_xiao())

XIAO_X, XIAO_Y = 0.0, 23.62
xiao = place(make_xiao(), "U2", "XIAO_ESP32C3", XIAO_X, XIAO_Y, 90, back=True)
xiao.Value().SetVisible(False)
setnets(xiao, {"13": "GND", "14": "VIN_MCU", "11": "DATA_3V3", "3": "BUTTON"})
silk_text("XIAO ESP32-C3 - USB zur Ausbuchtung", XIAO_X, XIAO_Y + 13.2, 1.2,
          pcbnew.B_SilkS, mirror=True)

# Schottky 5V -> XIAO 5V (USB am XIAO kann nicht in die LED-Leitung zurückspeisen)
pin5v = padxy(xiao, "14")
dsch = place(load("Diode_SMD", "D_SMA"), "D47", "SS34", -13.5, 34.0, 180)
setnets(dsch, {"1": "VIN_MCU", "2": "+5V"})
k = padxy(dsch, "1")
track("VIN_MCU", [k, (k[0] + 1.6, k[1]), (pin5v[0], k[1] - 0.3), pin5v], width=POWER_TRACK)

# --------------------------------------------------------------------------
# Pegelwandler 3,3V -> 5V + Serienwiderstand, Datenleitung zur ersten LED
# --------------------------------------------------------------------------
U1_X, U1_Y = 20.0, 31.5
u1 = place(load("Package_TO_SOT_SMD", "SOT-23-5"), "U1", "74AHCT1G125", U1_X, U1_Y, 0)
setnets(u1, {"1": "GND", "2": "DATA_3V3", "3": "GND", "4": "DATA_5V_R", "5": "+5V"})
for pn in ("1", "3"):  # /OE und GND
    px, py = padxy(u1, pn)
    sy = 1 if py > U1_Y else -1
    via("GND", px - 0.6, py + sy * 1.6)
    track("GND", [(px, py), (px - 0.6, py + sy * 1.6)], width=0.4)
cu1 = place(load("Capacitor_SMD", "C_0603_1608Metric"), "C48", "100nF",
            U1_X + 4.0, U1_Y - 1.9, 0)
setnets(cu1, {"1": "+5V", "2": "GND"})
c2p = padxy(cu1, "2")
via("GND", c2p[0], c2p[1] - 1.6)
track("GND", [c2p, (c2p[0], c2p[1] - 1.6)], width=0.4)
p5, c1p = padxy(u1, "5"), padxy(cu1, "1")
track("+5V", [p5, (p5[0] + 0.95, c1p[1]), c1p], width=0.4)

rser = place(load("Resistor_SMD", "R_0603_1608Metric"), "R1", "330R",
             U1_X + 4.2, U1_Y + 0.95, 0)
setnets(rser, {"1": "DATA_5V_R", "2": "DATA_5V"})
p4 = padxy(u1, "4")
r1a, r1b = padxy(rser, "1"), padxy(rser, "2")
track("DATA_5V_R", [p4, r1a])

# DATA_3V3: XIAO D10 -> Rückseite -> Via -> U1 A
p2 = padxy(u1, "2")
d10 = padxy(xiao, "11")
vA = (p2[0] - 2.4, p2[1])
track("DATA_3V3", [p2, vA])
via("DATA_3V3", *vA)
track("DATA_3V3", [vA, (vA[0], 35.6), (d10[0], 35.6), d10], layer=pcbnew.B_Cu)

# DATA_5V: R1 -> Via -> Rückseite -> Via an der Spitze -> erste LED
first = leds[0][0]
din1 = padxy(first, "4")
vB = (r1b[0] + 1.6, r1b[1])
track("DATA_5V", [r1b, vB])
via("DATA_5V", *vB)
vC = (din1[0] - 4.5, din1[1])
track("DATA_5V", [vB, (vB[0], 34.0), (vB[0] - 4.4, 38.4), (10.0, 38.4), (10.0, 47.5),
                  (vC[0] + 2.95, 47.5), (vC[0], 50.45), vC], layer=pcbnew.B_Cu)
via("DATA_5V", *vC)
track("DATA_5V", [vC, din1])

# --------------------------------------------------------------------------
# Taster (Rückseite) an XIAO D2
# --------------------------------------------------------------------------
btn = place(load("Button_Switch_THT", "SW_PUSH_6mm"), "SW1", "Effekt", 0, 0, 90, back=True)
bx = [unV(p.GetPosition()) for p in btn.Pads()]
cx = sum(p[0] for p in bx) / 4
cy = sum(p[1] for p in bx) / 4
btn.Move(V(28 - cx, 0 - cy) - V(0, 0))
setnets(btn, {"1": "BUTTON", "2": "GND"})
silk_text("EFFEKT", 28, -6.0, 1.2, pcbnew.B_SilkS, mirror=True)
b1 = sorted(unV(p.GetPosition()) for p in btn.Pads() if p.GetNumber() == "1")
track("BUTTON", [b1[0], b1[1]], layer=pcbnew.B_Cu)
d2 = padxy(xiao, "3")
bl = max(b1, key=lambda p: p[1])
track("BUTTON", [bl, (bl[0] - 3.75, bl[1] + 3.75), (d2[0], bl[1] + 3.75), d2],
      layer=pcbnew.B_Cu)

# --------------------------------------------------------------------------
# USB-C nur Strom (5V bis 3A) auf der linken 45°-Flanke,
# mittig zwischen den LEDs (-48|8) und (-32|24)
# --------------------------------------------------------------------------
OUT_N = (-1 / math.sqrt(2), 1 / math.sqrt(2))   # Flanke zeigt nach links unten
IN_N = (-OUT_N[0], -OUT_N[1])
FLANK_PT = (-40.0 + OUT_N[0] * 9.9, 16.0 + OUT_N[1] * 9.9)  # Punkt auf der Kante
USB_OVERHANG = 1.1  # Buchsenvorderkante steht so weit über die Platine
usb_o = (FLANK_PT[0] - OUT_N[0] * (3.65 - USB_OVERHANG),
         FLANK_PT[1] - OUT_N[1] * (3.65 - USB_OVERHANG))
usb = place(load("Connector_USB", "USB_C_Receptacle_HRO_TYPE-C-31-M-12"), "J1",
            "USB-C Power", usb_o[0], usb_o[1], 315)
setnets(usb, {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "S1": "GND",
              "A4": "+5V", "A9": "+5V", "B4": "+5V", "B9": "+5V",
              "A5": "CC1", "B5": "CC2"})
for item in list(usb.GraphicalItems()):  # Bestückungsdruck ragt über den Rand
    if item.GetLayer() == pcbnew.F_SilkS:
        usb.Remove(item)


def inward(p, d):
    return (p[0] + IN_N[0] * d, p[1] + IN_N[1] * d)


for g in ("A1", "B1"):  # GND-Pads direkt auf die Schirmlaschen
    gp = padxy(usb, g)
    sp = min((unV(p.GetPosition()) for p in usb.Pads() if p.GetNumber() == "S1"),
             key=lambda p: math.hypot(p[0] - gp[0], p[1] - gp[1]))
    track("GND", [gp, sp], width=0.4)
for v5 in ("A4", "A9"):  # VBUS etwas kräftiger in die 5V-Fläche führen
    vp = padxy(usb, v5)
    track("+5V", [vp, inward(vp, 3.2)], width=0.6)

for name, cc in (("R2", "CC1"), ("R3", "CC2")):
    ccp = padxy(usb, "A5" if cc == "CC1" else "B5")
    rc = inward(ccp, 5.5)
    r = place(load("Resistor_SMD", "R_0603_1608Metric"), name, "5k1", rc[0], rc[1], 45)
    setnets(r, {"1": cc, "2": "GND"})
    ra, rb = padxy(r, "1"), padxy(r, "2")
    track(cc, [ccp, ra], width=0.2)
    vg = inward(rb, 1.3)
    via("GND", *vg)
    track("GND", [rb, vg], width=0.4)

cusb = place(load("Capacitor_SMD", "C_0805_2012Metric"), "C49", "10uF", -32.0, 16.0, 0)
setnets(cusb, {"1": "+5V", "2": "GND"})
cp2 = padxy(cusb, "2")
via("GND", cp2[0], cp2[1] + 1.7)
track("GND", [cp2, (cp2[0], cp2[1] + 1.7)], width=0.5)

# Elko 1000 µF (Rückseite, THT) – Plus auf 5V-Fläche (oben), Minus auf GND (unten)
celko = place(load("Capacitor_THT", "CP_Radial_D10.0mm_P5.00mm"), "C50", "1000uF 10V",
              27.0, 16.0, 0, back=True)  # rechts vom XIAO – links braucht das USB-Kabel Platz
setnets(celko, {"1": "+5V", "2": "GND"})
silk_text("5V USB-C", -33.5, 20.0, 1.2, pcbnew.B_SilkS, mirror=True)

# --------------------------------------------------------------------------
# Befestigungslöcher
# --------------------------------------------------------------------------
for i, (x, y) in enumerate([(-40, -47), (40, -47), (0, -48)]):
    place(load("MountingHole", "MountingHole_3.2mm_M3"), f"H{i + 1}", "M3", x, y)

# --------------------------------------------------------------------------
# Beschriftung
# --------------------------------------------------------------------------
silk_text("<3 LED HEART <3", 0, -62.5, 2.5)
silk_text("LED Heart v1.0", 0, 0, 2.0, pcbnew.B_SilkS, mirror=True)
silk_text("2026", 0, 8.0 - 12.0, 1.2, pcbnew.B_SilkS, mirror=True)

# --------------------------------------------------------------------------
# Kupferflächen: oben +5V, unten GND
# --------------------------------------------------------------------------
for fp in board.GetFootprints():  # Abstand Kupferfläche <-> nicht durchkontaktierte Löcher
    for pad in fp.Pads():
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            pad.SetLocalClearance(mm(0.3))

for layer, name in ((pcbnew.F_Cu, "+5V"), (pcbnew.B_Cu, "GND")):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net(name))
    z.SetLocalClearance(mm(0.3))
    z.SetMinThickness(mm(0.25))
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.5))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIsFilled(False)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in outline:
        ol.Append(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))
    board.Add(z)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.BuildConnectivity()
pcbnew.SaveBoard(OUT, board)

# Kette für Firmware/Doku ausgeben
with open(os.path.join(HERE, "chain_order.txt"), "w") as f:
    f.write("# index col row  (Reihenfolge der Datenleitung)\n")
    for i, (c, r, _) in enumerate(order):
        f.write(f"{i} {c} {r}\n")

xs = [p[0] for p in outline]
ys = [p[1] for p in outline]
print(f"OK: {OUT}")
print(f"Platine {max(xs) - min(xs):.1f} x {max(ys) - min(ys):.1f} mm, {len(leds)} LEDs")
