import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from .const import DOMAIN, MANUFACTURER
from .core.models_zont import SensorZONT, DeviceZONT
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
):
    entry_id = config_entry.entry_id
    _LOGGER.debug(f'from sensor entry_id: {entry_id}')
    _LOGGER.debug(hass.data[DOMAIN][entry_id])

    devices = hass.data[DOMAIN][entry_id]

    for device in devices:
        sens = []
        sensors = device.sensors
        for sensor in sensors:
            unique_id = f'{entry_id}{device.id}{sensor.id}'
            sens.append(ZontSensor(device, sensor, unique_id))
        async_add_entities(sens)
        _LOGGER.debug(f'Добавлены сенсоры: {sens}')


class ZontSensor(Entity):

    def __init__(
            self, device: DeviceZONT,
            sensor: SensorZONT, unique_id: str
    ) -> None:
        self._device = device
        self._sensor = sensor
        self._unique_id = unique_id

    @property
    def name(self) -> str:
        name = f'{self._device.name}_{self._sensor.name}'
        return name

    @property
    def state(self) -> float | None:
        return self._sensor.value

    @property
    def unit_of_measurement(self) -> str | None:
        return self._sensor.unit

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def device_class(self) -> str | None:
        return self._sensor.type

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.id)},
            "name": self._device.name,
            "sw_version": None,
            "model": self._device.model,
            "manufacturer": MANUFACTURER,
        }
