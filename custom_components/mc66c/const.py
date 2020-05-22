from datetime import timedelta

DOMAIN = 'mc66c'

DEFAULT_NAME = 'mc66c'
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

# See page 9 in 5511- 634 GB Rev C1.qxd.pdf -  1.4. Display function.
SENSOR_TYPES = {
    'energy': ['Energy', 'GJ', 'mdi:radiator'],
    'volume': ['Volume',  'M3', 'mdi:water'],
    'op_hrs': ['Operating hours', 'hrs', 'mdi:timer-sand'],
    'temperature_in': ['Temperature in', '°C', 'mdi:coolant-temperature'],
    'temperature_out': ['Temperature out', '°C', 'mdi:coolant-temperature'],
    'temperature_diff': ['Temperature difference', '°C', 'mdi:coolant-temperature'],
    'power': ['Power', 'kW', 'mdi:flash'],
    'peak_power': ['Peak power', 'kWp', 'mdi:flash'],
    'flow': ['Flow', 'l/h', 'mdi:water'],
}