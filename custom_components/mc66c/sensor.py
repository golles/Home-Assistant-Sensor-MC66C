"""
configuration.yaml / packages/stadsverwarming.yaml

sensor:
  - platform: mc66c
    name: Stadsverwarming
    port: /dev/ttyUSB1
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
import voluptuous as vol
import serial
from time import sleep

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_PORT,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_RESOURCES
)
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity
from .const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    SENSOR_TYPES,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_PORT): cv.string,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
    vol.Required(CONF_RESOURCES, default=[]):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the sensors."""
    name = config.get(CONF_NAME)
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
                sensor_type.title(), "", "mdi:eye"]

        entities.append(MC66CSensor(name, data, sensor_type))

    add_entities(entities)


class MC66CData(object):
    """Representation of the data from the MC66C."""

    def __init__(self, port):
        """Initialize the serial reader."""
        self._port = port
        self.data = None

    @Throttle(DEFAULT_SCAN_INTERVAL)
    def update(self):
        """Update the data from the serial port."""
        # See page 33-36 in 5511- 634 GB Rev C1.qxd.pdf -  4. Data communication.
        mc66c = serial.Serial(port=self._port,
                              bytesize=serial.SEVENBITS,
                              parity=serial.PARITY_EVEN,
                              stopbits=serial.STOPBITS_TWO,
                              timeout=2)
        mc66c.baudrate = 300
        mc66c.write("/#1".encode("utf-8"))
        mc66c.flush()
        sleep(1)
        mc66c.baudrate = 1200
        mc66c.flushInput()
        new_data = mc66c.read(87).split()
        mc66c.close()

        if len(new_data) == 10:
            self.data = new_data
            _LOGGER.info("Successfully fetched new data: %s", self.data)
        else:
            _LOGGER.warning("Skipping, incomplete data: %s", self.data)


class MC66CSensor(Entity):
    """Representation of a sensor."""

    def __init__(self, name, data, sensor_type):
        """Initialize the sensor."""
        self.data = data
        self.type = sensor_type

        self._name = "{} {}".format(name, SENSOR_TYPES[self.type][0])
        self._unit_of_measurement = SENSOR_TYPES[self.type][1]
        self._icon = SENSOR_TYPES[self.type][2]
        self._state = None
        self._unique_id = "{}_{}_{}".format(DOMAIN, name, SENSOR_TYPES[self.type][0])

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

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._unique_id

    def update(self):
        """Get the data and use it to update our sensor state."""
        self.data.update()

        try:
            if self.type == "energy":
                self._state = int((self.data.data[0]).decode("utf-8")) / 1000
            elif self.type == "volume":
                self._state = int((self.data.data[1]).decode("utf-8")) / 1000
            elif self.type == "op_hrs":
                self._state = int((self.data.data[2]).decode("utf-8"))
            elif self.type == "temperature_in":
                self._state = int((self.data.data[3]).decode("utf-8")) / 100
            elif self.type == "temperature_out":
                self._state = int((self.data.data[4]).decode("utf-8")) / 100
            elif self.type == "temperature_diff":
                self._state = int((self.data.data[5]).decode("utf-8")) / 100
            elif self.type == "power":
                self._state = int((self.data.data[6]).decode("utf-8")) / 10
            elif self.type == "flow":
                self._state = int((self.data.data[7]).decode("utf-8")) / 10
            elif self.type == "peak_power":
                self._state = int((self.data.data[8]).decode("utf-8")) / 10
        except Exception as error:
            _LOGGER.error("Error=%s parsing data=%s", error, self.data.data)
