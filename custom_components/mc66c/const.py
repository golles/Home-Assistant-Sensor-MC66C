"""Constants for component."""
from datetime import timedelta

DOMAIN = "mc66c"

DEFAULT_NAME = "mc66c"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

# See page 9 in 5511- 634 GB Rev C1.qxd.pdf -  1.4. Display function.
# Format: data position, name, unit, icon.
SENSOR_TYPES = {
    "energy": [0, "Energy", "GJ", "mdi:radiator"],
    "volume": [1, "Volume", "M3", "mdi:water"],
    "op_hrs": [2, "Operating hours", "hrs", "mdi:timer-sand"],
    "temperature_in": [3, "Temperature in", "°C", "mdi:coolant-temperature"],
    "temperature_out": [4, "Temperature out", "°C", "mdi:coolant-temperature"],
    "temperature_diff": [5, "Temperature difference", "°C", "mdi:coolant-temperature"],
    "power": [6, "Power", "kW", "mdi:flash"],
    "flow": [7, "Flow", "l/h", "mdi:water"],
    "peak_power": [8, "Peak power", "kWp", "mdi:flash"],
    "info_code": [9, "Info code", "", "mdi:alert-outline"],
}
