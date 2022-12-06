"""Constants for component."""
import logging
from time import sleep

import homeassistant.helpers.config_validation as cv
import serial
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_PORT, CONF_RESOURCES, CONF_SCAN_INTERVAL
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

from .const import DEFAULT_NAME, DEFAULT_SCAN_INTERVAL, DOMAIN, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_PORT): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
        vol.Required(CONF_RESOURCES, default=[]): vol.All(
            cv.ensure_list, [vol.In(SENSOR_TYPES)]
        ),
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the sensors."""
    name = config.get(CONF_NAME)
    port = config.get(CONF_PORT)

    try:
        reader = MC66CReader(port)
    except Exception:
        _LOGGER.error("Unable to connect to %s", port)
        return False

    entities = []

    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()

        if sensor_type not in SENSOR_TYPES:
            SENSOR_TYPES[sensor_type] = [sensor_type.title(), "", "mdi:eye"]

        entities.append(MC66CSensor(name, reader, sensor_type))

    add_entities(entities)


class MC66CReader(object):
    """Reader object that communicates with the MC66C."""

    def __init__(self, port):
        """Initialize the serial reader."""
        self._port = port
        self.data = None

    @Throttle(DEFAULT_SCAN_INTERVAL)
    def read(self):
        """Read data from the serial port."""
        # See page 33-36 in 5511- 634 GB Rev C1.qxd.pdf -  4. Data communication.
        mc66c = serial.Serial(
            port=self._port,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_TWO,
            timeout=2,
        )
        mc66c.baudrate = 300
        mc66c.write("/#1".encode("utf-8"))
        mc66c.flush()
        sleep(1)
        mc66c.baudrate = 1200
        mc66c.flushInput()
        reading = mc66c.read(87).split()
        mc66c.close()

        self.validate_and_set_data(reading)

    def validate_and_set_data(self, reading):
        """New data needs validation before we continue."""
        data = []

        num_fields = len(reading)
        if num_fields is 10:
            _LOGGER.info("Successfully fetched new data: %s", reading)

            try:
                for c in reading:
                    if (len(c)) != 7:
                        raise Exception("Received invalid data field length")

                data.append(int((reading[0]).decode("utf-8")) / 1000)  # Energy.
                data.append(int((reading[1]).decode("utf-8")) / 1000)  # Volume.
                data.append(int((reading[2]).decode("utf-8")))  # Op_hrs.
                data.append(int((reading[3]).decode("utf-8")) / 100)  # Temperature_in.
                data.append(int((reading[4]).decode("utf-8")) / 100)  # Temperature_out.
                data.append(
                    int((reading[5]).decode("utf-8")) / 100
                )  # Temperature_diff.
                data.append(int((reading[6]).decode("utf-8")) / 10)  # Power.
                data.append(int((reading[7]).decode("utf-8")) / 10)  # Flow.
                data.append(int((reading[8]).decode("utf-8")) / 10)  # Peak_power.
                data.append(int((reading[9]).decode("utf-8")))  # Info_code

                # Only setting the data at the end, if parsing fails for one or more sensors,
                # the data was corrupt and this reading should be skipped.
                self.data = data
            except Exception as error:
                _LOGGER.info("Error=%s parsing data=%s", error, reading)
        else:
            _LOGGER.info(
                "Skipping, received %s fields, this should be 10. Data: %s",
                num_fields,
                reading,
            )


class MC66CSensor(Entity):
    """Representation of a sensor."""

    def __init__(self, name, reader, sensor_type):
        """Initialize the sensor."""
        self.reader = reader
        self.type = sensor_type

        self._data_position = SENSOR_TYPES[self.type][0]
        self._name = "{} {}".format(name, SENSOR_TYPES[self.type][1])
        self._unit_of_measurement = SENSOR_TYPES[self.type][2]
        self._icon = SENSOR_TYPES[self.type][3]
        self._state = None
        self._unique_id = "{}_{}_{}".format(DOMAIN, name, SENSOR_TYPES[self.type][1])

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
        self.reader.read()

        if self.reader.data is not None:
            new_state = self.reader.data[self._data_position]

            if (
                self._state is not None
                and self._data_position is 0
                and abs(new_state - self._state) / self._state > 1
            ):
                _LOGGER.info(
                    "Skipping energy update; new value: %s is much different than previous: %s",
                    new_state,
                    self._state,
                )
            else:
                self._state = new_state
