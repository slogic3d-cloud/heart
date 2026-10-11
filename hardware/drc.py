#!/usr/bin/env python3
"""DRC über die KiCad-Python-API: python3 hardware/drc.py"""
import os, sys
os.environ.setdefault("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
b = pcbnew.LoadBoard(os.path.join(HERE, "heart.kicad_pcb"))
rep = os.path.join(HERE, "drc_report.txt")
pcbnew.WriteDRCReport(b, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
txt = open(rep).read()
print(txt)
bad = [l for l in txt.splitlines() if l.startswith("**") and "Found 0" not in l]
sys.exit(1 if bad else 0)
