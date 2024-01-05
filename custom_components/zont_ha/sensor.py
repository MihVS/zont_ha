import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from .const import DOMAIN
from .core.models_zont import SensorZONT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
):
    _LOGGER.error(
        f'Уже добавленные сенсоры: '
        f'{hass.config_entries}'
    )
    accounts = hass.data[DOMAIN]
    account_id = len(accounts) - 1
    devices = accounts[account_id]

    for device_id, device in devices.items():
        sens = []
        sensors = device.sensors
        name_device = device.name
        for sensor in sensors:
            unique_id = f'{account_id}{device_id}{sensor.id}'
            sens.append(ZontSensor(name_device, sensor, unique_id))
        async_add_entities(sens)
        # _LOGGER.debug(
        #     f'Уже добавленные сенсоры: '
        #     f'{hass.data[DOMAIN][config_entry.unique_id]}'
        # )



class ZontSensor(Entity):

    def __init__(
            self, _name_device: str, sensor: SensorZONT, unique_id: str
    ) -> None:
        self._sensor = sensor
        self._unique_id = unique_id
        self._name_device = _name_device

    @property
    def name(self) -> str:
        name = f'{self._name_device}_{self._sensor.name}'
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

