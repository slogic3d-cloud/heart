#!/usr/bin/env python3
"""
Erzeugt den KiCad-Schaltplan hardware/heart.kicad_sch (KiCad 7+).

    python3 hardware/gen_sch.py

Netznamen und Footprints sind exakt dieselben wie in gen_pcb.py, und jedes
Bauteil bekommt eine feste ID (uuid5 aus der Referenz). gen_pcb.py setzt
dieselbe ID in die Footprints – dadurch sind Schaltplan und Platine verknüpft
und "Platine aus Schaltplan aktualisieren" (F8) in KiCad funktioniert.
"""
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sexpr import Q, dump, find, first, parse  # noqa: E402
from netlist import COMPONENTS, ROOT_UUID, ref_uuid  # noqa: E402

SYMDIR = os.environ.get("KICAD7_SYMBOL_DIR", "/usr/share/kicad/symbols")
OUT = os.path.join(HERE, "heart.kicad_sch")

_uid_counter = [0]


def uid(key=None):
    if key is None:
        _uid_counter[0] += 1
        key = f"auto/{_uid_counter[0]}"
    return Q(str(uuid.uuid5(uuid.NAMESPACE_URL, "heart-led-sch/" + key)))


def grid(v):
    return round(v / 1.27) * 1.27


# --------------------------------------------------------------------------
# Symbole aus den KiCad-Bibliotheken holen (und "extends" auflösen)
# --------------------------------------------------------------------------
_libcache = {}


def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib == "heart":
        path = os.path.join(HERE, "heart.kicad_sym")
    else:
        path = os.path.join(SYMDIR, lib + ".kicad_sym")
    if path not in _libcache:
        _libcache[path] = {s[1]: s for s in find(parse(open(path).read())[0], "symbol")}
    syms = _libcache[path]
    s = [e for e in syms[name]]
    ext = first(s, "extends")
    if ext:  # abgeleitetes Symbol: Grafik vom Eltern-Symbol, Felder vom Kind
        parent = lib_symbol(f"{lib}:{ext[1]}")
        own = {p[1]: p for p in find(s, "property")}
        flat = [parent[0], Q(name)]
        for e in parent[2:]:
            if isinstance(e, list) and e[0] == "property" and e[1] in own:
                flat.append(own.pop(e[1]))
            elif isinstance(e, list) and e[0] == "symbol":
                sub = list(e)
                sub[1] = Q(sub[1].replace(ext[1], name, 1))
                flat.append(sub)
            else:
                flat.append(e)
        flat[2:2] = list(own.values())
        s = flat
    return s


def embedded(lib_id):
    s = list(lib_symbol(lib_id))
    s[1] = Q(lib_id)
    return s


def pins_of(sym):
    """[(nummer, name, x, y, winkel, versteckt)] in Symbolkoordinaten (y nach oben)"""
    out = []
    for unit in find(sym, "symbol"):
        for p in find(unit, "pin"):
            at = first(p, "at")
            out.append((first(p, "number")[1], first(p, "name")[1],
                        float(at[1]), float(at[2]), int(float(at[3])), "hide" in p))
    return out


# --------------------------------------------------------------------------
# Schaltplan-Elemente
# --------------------------------------------------------------------------
items = []
lib_ids = set()
pwr_count = [0]


def font(size=1.27):
    return ["font", ["size", size, size]]


def prop(name, value, x, y, hide=False, angle=0, justify=None):
    eff = ["effects", font()]
    if justify:
        eff.append(["justify", justify])
    if hide:
        eff.append("hide")
    return ["property", Q(name), Q(value), ["at", x, y, angle], eff]


def place_symbol(lib_id, ref, value, x, y, footprint="", fields=None, key=None,
                 ref_pos=None, val_pos=None, hide_ref=False, just=None):
    lib_ids.add(lib_id)
    sym = lib_symbol(lib_id)
    u = Q(ref_uuid(ref)) if key is None else uid(key)
    rp = ref_pos or (x, y - 2.54)
    vp = val_pos or (x, y + 2.54)
    node = ["symbol", ["lib_id", Q(lib_id)], ["at", x, y, 0], ["unit", 1],
            ["in_bom", "no" if ref.startswith("#") else "yes"],
            ["on_board", "no" if ref.startswith("#") else "yes"],
            ["dnp", "no"], ["uuid", u],
            prop("Reference", ref, rp[0], rp[1], hide=hide_ref, justify=just),
            prop("Value", value, vp[0], vp[1], justify=just),
            prop("Footprint", footprint, x, y, hide=True),
            prop("Datasheet", "", x, y, hide=True)]
    for k, v in (fields or {}).items():
        node.append(prop(k, v, x, y, hide=True))
    for num, *_ in pins_of(sym):
        node.append(["pin", Q(num), ["uuid", uid(f"{u}/pin/{num}")]])
    node.append(["instances", ["project", Q("heart"),
                               ["path", Q("/" + ROOT_UUID), ["reference", Q(ref)], ["unit", 1]]]])
    items.append(node)
    return sym


def wire(x1, y1, x2, y2):
    items.append(["wire", ["pts", ["xy", x1, y1], ["xy", x2, y2]],
                  ["stroke", ["width", 0], ["type", "default"]], ["uuid", uid()]])


def power(name, x, y):
    pwr_count[0] += 1
    lib = "power:" + name
    ref = f"#PWR{pwr_count[0]:03d}" if name != "PWR_FLAG" else f"#FLG{pwr_count[0]:03d}"
    angle_val = (x, y - 3.81) if name == "+5V" else (x, y + 3.81)
    place_symbol(lib, ref, name, x, y, key=f"pwr/{ref}", hide_ref=True,
                 val_pos=angle_val if name != "PWR_FLAG" else (x, y - 4.445))


def glabel(name, x, y, outward):
    ang, just = {(1, 0): (0, "left"), (-1, 0): (180, "right"),
                 (0, -1): (90, "left"), (0, 1): (270, "right")}[outward]
    items.append(["global_label", Q(name), ["shape", "bidirectional"], ["at", x, y, ang],
                  ["fields_autoplaced"], ["effects", font(), ["justify", just]], ["uuid", uid()],
                  ["property", Q("Intersheetrefs"), Q("${INTERSHEET_REFS}"), ["at", x, y, 0],
                   ["effects", font(), "hide"]]])


def no_connect(x, y):
    items.append(["no_connect", ["at", x, y], ["uuid", uid()]])


def text(t, x, y, size=2.0, bold=False):
    f = ["font", ["size", size, size]] + (["bold"] if bold else [])
    items.append(["text", Q(t), ["at", x, y, 0], ["effects", f, ["justify", "left", "bottom"]],
                  ["uuid", uid()]])


def connect(sym, x, y, netmap, stub=2.54):
    """Verbindet jeden Pin: Stummel + Power-Symbol / Netzlabel, sonst No-Connect."""
    done = set()
    for num, _name, px, py, ang, _hide in pins_of(sym):
        sx, sy = x + px, y - py
        key = (round(sx, 2), round(sy, 2))
        if key in done:  # gestapelte Pins (z.B. USB-C GND/VBUS) nur einmal
            continue
        done.add(key)
        net = netmap.get(num)
        if net is None:
            no_connect(sx, sy)
            continue
        ox, oy = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[ang]
        length = stub
        if net in ("+5V", "GND"):
            if ox:  # seitlicher Pin: Symbol etwas weiter weg
                length = 5.08
            elif (net == "GND") == (oy < 0):  # Symbol würde zurück aufs Bauteil zeigen
                length = 7.62
        ex, ey = sx + ox * length, sy + oy * length
        wire(sx, sy, ex, ey)
        if net in ("+5V", "GND"):
            power(net, ex, ey)
        else:
            glabel(net, ex, ey, (ox, oy))


def part(ref, x, y, **kw):
    c = COMPONENTS[ref]
    x, y = grid(x), grid(y)
    sym = place_symbol(c["symbol"], ref, c["value"], x, y, c["footprint"],
                       {"LCSC": c["lcsc"]} if c.get("lcsc") else None, **kw)
    if c["nets"] is not None:
        connect(sym, x, y, c["nets"])
    return sym


# --------------------------------------------------------------------------
# Blatt aufbauen (A2)
# --------------------------------------------------------------------------
text("LED-Herz – Schaltplan", 25.4, 22.86, 4, True)
text("46 × WS2812B, Seeed XIAO ESP32-C3, USB-C (nur Strom). Netze sind über Labels verbunden.",
     25.4, 30.48, 2)

# Stromversorgung
text("Stromversorgung (USB-C 5V)", 25.4, 48.26, 2.5, True)
part("J1", 45.72, 83.82, ref_pos=(45.72, 53.34), val_pos=(45.72, 57.15))
part("R2", 99.06, 76.2, ref_pos=(102.87, 74.93), val_pos=(102.87, 77.47))
part("R3", 116.84, 76.2, ref_pos=(120.65, 74.93), val_pos=(120.65, 77.47))
part("C49", 137.16, 76.2, ref_pos=(140.97, 74.93), val_pos=(140.97, 77.47))
part("C50", 157.48, 76.2, ref_pos=(161.29, 74.93), val_pos=(161.29, 77.47))
# PWR_FLAGs: sagen der ERC, dass +5V und GND von der Buchse kommen
for net, fy in (("+5V", 99.06), ("GND", 111.76)):
    fx = 78.74
    power(net, fx, fy)
    wire(fx, fy, fx + 7.62, fy)
    power("PWR_FLAG", fx + 7.62, fy)

# Mikrocontroller
text("Mikrocontroller (steckt hinten)", 190.5, 48.26, 2.5, True)
part("D47", 203.2, 63.5, ref_pos=(203.2, 59.69), val_pos=(203.2, 67.31))
part("U2", 233.68, 86.36, ref_pos=(233.68, 72.39), val_pos=(233.68, 100.33))
part("SW1", 233.68, 119.38, ref_pos=(233.68, 114.3), val_pos=(233.68, 123.19))
text("Taster gegen GND, Pull-up im ESP32", 215.9, 130.81, 1.5)

# Pegelwandler
text("Pegelwandler 3,3V -> 5V", 304.8, 48.26, 2.5, True)
part("U1", 325.12, 83.82, ref_pos=(330.2, 69.85), val_pos=(330.2, 97.79))
part("C48", 363.22, 83.82, ref_pos=(367.03, 82.55), val_pos=(367.03, 85.09))
part("R1", 391.16, 83.82, ref_pos=(394.97, 82.55), val_pos=(394.97, 85.09))
text("R1 dämpft Reflexionen auf der Datenleitung", 381.0, 106.68, 1.5)

# Befestigungslöcher
text("Befestigung", 444.5, 48.26, 2.5, True)
for i, ref in enumerate(("H1", "H2", "H3")):
    part(ref, 450.85 + i * 20.32, 66.04, ref_pos=(450.85 + i * 20.32 + 3.81, 64.77),
         val_pos=(450.85 + i * 20.32 + 3.81, 67.31))

# LED-Matrix
text("LED-Kette (Start an der Herzspitze, Schlangenlinie nach oben)", 25.4, 147.32, 2.5, True)
text("Jede LED hat einen eigenen 100nF direkt daneben (C1…C46).", 25.4, 153.67, 1.5)
leds = sorted((r for r in COMPONENTS if r.startswith("D") and COMPONENTS[r]["value"] == "WS2812B"),
              key=lambda r: int(r[1:]))
PER_ROW, PX, PY = 8, 68.58, 40.64
for i, ref in enumerate(leds):
    n = int(ref[1:])
    x = 45.72 + (i % PER_ROW) * PX
    y = 175.26 + (i // PER_ROW) * PY
    part(ref, x, y, ref_pos=(x + 6.35, y - 6.35), val_pos=(x + 6.35, y + 6.35), just="left")
    part(f"C{n}", x + 34.29, y, ref_pos=(x + 38.1, y - 1.27), val_pos=(x + 38.1, y + 1.27))

# --------------------------------------------------------------------------
sch = ["kicad_sch", ["version", 20230121], ["generator", "eeschema"],
       ["uuid", Q(ROOT_UUID)], ["paper", Q("A2")],
       ["title_block", ["title", Q("LED-Herz")], ["date", Q("2026-10-11")], ["rev", Q("1.0")],
        ["comment", 1, Q("46 x WS2812B, XIAO ESP32-C3, USB-C")],
        ["comment", 2, Q("erzeugt mit hardware/gen_sch.py")]],
       ["lib_symbols"] + [embedded(l) for l in sorted(lib_ids)]]
sch += items
sch.append(["sheet_instances", ["path", Q("/"), ["page", Q("1")]]])

with open(OUT, "w") as f:
    f.write(dump(sch) + "\n")
print(f"OK: {OUT}  ({len([c for c in COMPONENTS])} Bauteile)")
