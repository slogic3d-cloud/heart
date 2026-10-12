#!/usr/bin/env python3
"""
Prüft, dass Schaltplan und Platine zusammenpassen:

    python3 hardware/check_sch.py

- KiCad exportiert die Netzliste aus heart.kicad_sch
- für jedes Bauteil: gleicher Footprint, gleicher Wert, gleiche Verknüpfung (UUID)
- für jedes Pad: gleiches Netz wie auf der Platine
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
import pcbnew  # noqa: E402
from sexpr import find, first, parse  # noqa: E402

errors = []

with tempfile.TemporaryDirectory() as td:
    net = os.path.join(td, "heart.net")
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "-o", net,
                    os.path.join(HERE, "heart.kicad_sch")], check=True, capture_output=True)
    tree = parse(open(net).read())[0]

comps = {}
for c in find(first(tree, "components"), "comp"):
    ref = first(c, "ref")[1]
    comps[ref] = {"value": first(c, "value")[1], "footprint": first(c, "footprint")[1],
                  "uuid": first(c, "tstamps")[1] if first(c, "tstamps") else None}

sch_pin = {}  # (ref, pin) -> netname
for n in find(first(tree, "nets"), "net"):
    name = first(n, "name")[1]
    nodes = find(n, "node")
    for nd in nodes:
        key = (first(nd, "ref")[1], first(nd, "pin")[1])
        sch_pin[key] = None if name.startswith("unconnected-") else name

board = pcbnew.LoadBoard(os.path.join(HERE, "heart.kicad_pcb"))
pcb_pin = {}
pcb_fp = {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    lib = fp.GetFPID()
    pcb_fp[ref] = {"value": fp.GetValue(),
                   "footprint": f"{lib.GetLibNickname().wx_str()}:{lib.GetLibItemName().wx_str()}",
                   "path": fp.GetPath().AsString()}
    for pad in fp.Pads():
        if not pad.GetNumber():
            continue
        name = pad.GetNetname() or None
        key = (ref, pad.GetNumber())
        if pcb_pin.get(key) not in (None, name):
            errors.append(f"{ref}.{pad.GetNumber()}: Pads mit gleicher Nummer in verschiedenen Netzen")
        pcb_pin[key] = name or pcb_pin.get(key)

for ref in sorted(set(comps) | set(pcb_fp)):
    if ref not in pcb_fp:
        errors.append(f"{ref}: im Schaltplan, fehlt auf der Platine")
        continue
    if ref not in comps:
        errors.append(f"{ref}: auf der Platine, fehlt im Schaltplan")
        continue
    s, p = comps[ref], pcb_fp[ref]
    if s["footprint"] != p["footprint"]:
        errors.append(f"{ref}: Footprint Schaltplan {s['footprint']} != Platine {p['footprint']}")
    if s["value"] != p["value"]:
        errors.append(f"{ref}: Wert Schaltplan {s['value']} != Platine {p['value']}")
    if s["uuid"] and p["path"].strip("/") != s["uuid"]:
        errors.append(f"{ref}: nicht verknüpft (Platine {p['path']}, Schaltplan /{s['uuid']})")

for key in sorted(set(sch_pin) | set(pcb_pin)):
    if key[0] not in comps or key[0] not in pcb_fp:
        continue
    a, b = sch_pin.get(key), pcb_pin.get(key)
    if a != b:
        errors.append(f"{key[0]}.{key[1]}: Schaltplan {a or '(offen)'} != Platine {b or '(offen)'}")

nets = sorted({v for v in sch_pin.values() if v})
print(f"{len(comps)} Bauteile, {len(nets)} Netze, {len(sch_pin)} Pins verglichen")
if errors:
    print("FEHLER:")
    for e in errors:
        print("  " + e)
    sys.exit(1)
print("OK: Schaltplan und Platine stimmen überein")
