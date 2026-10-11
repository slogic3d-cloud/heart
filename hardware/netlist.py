"""
Gemeinsame Bauteil- und Netzliste für Schaltplan (gen_sch.py) und Prüfung (check_sch.py).
Die Netznamen sind identisch mit denen, die gen_pcb.py auf der Platine vergibt.
"""
import uuid

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
NUM_LEDS = sum(row.count("X") for row in MASK)

# Feste IDs: Schaltplan-Symbol und Platinen-Footprint bekommen dieselbe UUID
ROOT_UUID = str(uuid.uuid5(uuid.NAMESPACE_URL, "heart-led-sch/root"))


def ref_uuid(ref):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "heart-led-sch/sym/" + ref))


def _c(symbol, value, footprint, nets, lcsc=None):
    return {"symbol": symbol, "value": value, "footprint": footprint, "nets": nets, "lcsc": lcsc}


COMPONENTS = {}
for n in range(1, NUM_LEDS + 1):
    COMPONENTS[f"D{n}"] = _c(
        "LED:WS2812B", "WS2812B", "LED_SMD:LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm",
        {"1": "+5V", "3": "GND",
         "4": "DATA_5V" if n == 1 else f"LED{n - 1}_DOUT",
         "2": f"LED{n}_DOUT" if n < NUM_LEDS else None}, "C114586")
    COMPONENTS[f"C{n}"] = _c("Device:C", "100nF", "Capacitor_SMD:C_0603_1608Metric",
                             {"1": "+5V", "2": "GND"}, "C14663")

COMPONENTS.update({
    "C48": _c("Device:C", "100nF", "Capacitor_SMD:C_0603_1608Metric",
              {"1": "+5V", "2": "GND"}, "C14663"),
    "C49": _c("Device:C", "10uF", "Capacitor_SMD:C_0805_2012Metric",
              {"1": "+5V", "2": "GND"}, "C15850"),
    "C50": _c("Device:C_Polarized", "1000uF 10V", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
              {"1": "+5V", "2": "GND"}),
    "D47": _c("Device:D_Schottky", "SS34", "Diode_SMD:D_SMA",
              {"1": "VIN_MCU", "2": "+5V"}, "C408258"),
    "U1": _c("74xGxx:74AHCT1G125", "74AHCT1G125", "Package_TO_SOT_SMD:SOT-23-5",
             {"1": "GND", "2": "DATA_3V3", "3": "GND", "4": "DATA_5V_R", "5": "+5V"}, "C7484"),
    "R1": _c("Device:R", "330R", "Resistor_SMD:R_0603_1608Metric",
             {"1": "DATA_5V_R", "2": "DATA_5V"}, "C23138"),
    "R2": _c("Device:R", "5k1", "Resistor_SMD:R_0603_1608Metric",
             {"1": "CC1", "2": "GND"}, "C23186"),
    "R3": _c("Device:R", "5k1", "Resistor_SMD:R_0603_1608Metric",
             {"1": "CC2", "2": "GND"}, "C23186"),
    "J1": _c("Connector:USB_C_Receptacle_USB2.0_16P", "USB-C Power",
             "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
             {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "S1": "GND",
              "A4": "+5V", "A9": "+5V", "B4": "+5V", "B9": "+5V",
              "A5": "CC1", "B5": "CC2"}, "C165948"),
    "U2": _c("heart:XIAO_ESP32C3", "XIAO_ESP32C3", "heart:Seeed_XIAO_Socket",
             {"13": "GND", "14": "VIN_MCU", "11": "DATA_3V3", "3": "BUTTON"}),
    "SW1": _c("Switch:SW_Push", "Effekt", "Button_Switch_THT:SW_PUSH_6mm",
              {"1": "BUTTON", "2": "GND"}),
})
for i in range(1, 4):
    COMPONENTS[f"H{i}"] = _c("Mechanical:MountingHole", "M3",
                             "MountingHole:MountingHole_3.2mm_M3", {})
