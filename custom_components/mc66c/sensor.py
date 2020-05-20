"""
configuration.yaml / packages/stadsverwarming.yaml

sensor:
  - platform: mc66c
    port: '/dev/ttyUSB1'
    scan_interval: 30
    resources:
      - energy
      - volume
      - op_hrs
      - temperature_in
      - temperature_out
      - temperature_diff
      - power
      - flow
      - peak_power

group:
  mc66c:
    name: Stadsverwarming meter
    entities:
      - sensor.mc66c_energy
      - sensor.mc66c_volume
      - sensor.mc66c_operating_hours
      - sensor.mc66c_temperature_in
      - sensor.mc66c_temperature_out
      - sensor.mc66c_temperature_difference
      - sensor.mc66c_power
      - sensor.mc66c_peak_power
      - sensor.mc66c_flow
"""

import logging
from datetime import timedelta
import voluptuous as vol
import serial
from time import sleep

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
        CONF_PORT, CONF_RESOURCES
    )
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)
SENSOR_PREFIX = 'mc66c '
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

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PORT): cv.string,
    vol.Required(CONF_RESOURCES, default=[]):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the sensors."""
    port = config.get(CONF_PORT)

    try:
        data = MC66CData(port)
    except RunTimeError:
        _LOGGER.error("Unable to connect to %s", port)
        return False

    entities = []

    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()

        if sensor_type not in SENSOR_TYPES:
            SENSOR_TYPES[sensor_type] = [
                sensor_type.title(), '', 'mdi:eye']

        entities.append(MC66CSensor(data, sensor_type))

    add_entities(entities)

class MC66CData(object):
    """Representation of the data from the MC66C."""

    def __init__(self, port):
        """Initialize the portal."""
        self._port = port
        self.data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update the data from the portal."""
        # See page 33-36 in 5511- 634 GB Rev C1.qxd.pdf -  4. Data communication.

        # Thank you @RuntimeError123 for the following 13 lines of code!
        mc66c = serial.Serial(port=self._port,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=2)
        mc66c.baudrate = 300
        mc66c.write('/#1'.encode('utf-8'))
        mc66c.flush()
        sleep(1)
        mc66c.baudrate = 1200
        mc66c.flushInput()
        self.data = mc66c.read(87).split()
        mc66c.close()

        _LOGGER.debug("Data = %s", self.data)


class MC66CSensor(Entity):
    """Representation of a sensor."""

    def __init__(self, data, sensor_type):
        """Initialize the sensor."""
        self.data = data
        self.type = sensor_type
        self._name = SENSOR_PREFIX + SENSOR_TYPES[self.type][0]
        self._unit_of_measurement = SENSOR_TYPES[self.type][1]
        self._icon = SENSOR_TYPES[self.type][2]
        self._state = None
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    def update(self):
        """Get the latest data and use it to update our sensor state."""
        self.data.update()

        if self.type == 'energy':
            self._state = int((self.data.data[0]).decode('utf-8'))/1000
        elif self.type == 'volume':
            self._state = int((self.data.data[1]).decode('utf-8'))/1000
        elif self.type == 'op_hrs':
            self._state = int((self.data.data[2]).decode('utf-8'))
        elif self.type == 'temperature_in':
            self._state = int((self.data.data[3]).decode('utf-8'))/100
        elif self.type == 'temperature_out':
            self._state = int((self.data.data[4]).decode('utf-8'))/100
        elif self.type == 'temperature_diff':
            self._state = int((self.data.data[5]).decode('utf-8'))/100
        elif self.type == 'power':
            self._state = int((self.data.data[6]).decode('utf-8'))/10
        elif self.type == 'flow':
            self._state = int((self.data.data[7]).decode('utf-8'))/10
        elif self.type == 'peak_power':
            self._state = int((self.data.data[8]).decode('utf-8'))/10
