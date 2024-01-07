import logging

import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from .const import DOMAIN, MANUFACTURER, ZONT
from .core.models_zont import SensorZONT, DeviceZONT
from datetime import timedelta

SCAN_INTERVAL = timedelta(seconds=30)

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

    zont = hass.data[DOMAIN][entry_id]
    coordinator = ZontCoordinator(hass, zont)

    await coordinator.async_config_entry_first_refresh()

    for device in zont.data.devices:
        sens = []
        sensors = device.sensors
        for sensor in sensors:
            unique_id = f'{entry_id}{device.id}{sensor.id}'
            sens.append(ZontSensor(coordinator, device, sensor, unique_id))
        async_add_entities(sens)
        _LOGGER.debug(f'Добавлены сенсоры: {sens}')


class ZontCoordinator(DataUpdateCoordinator):
    """Координатор для общего обновления данных"""

    def __init__(self, hass, zont):
        super().__init__(
            hass,
            _LOGGER,
            name="ZONT",
            update_interval=timedelta(seconds=60),
        )
        self.zont = zont

    async def _async_update_data(self):
        """Обновление данных API zont"""
        try:
            async with async_timeout.timeout(10):
                await self.zont.get_update()
                return self.zont

        except Exception as err:
            raise UpdateFailed(f"Ошибка соединения с API zont: {err}")


class ZontSensor(CoordinatorEntity, Entity):

    def __init__(
            self, coordinator, device: DeviceZONT,
            sensor: SensorZONT, unique_id: str
    ) -> None:
        super().__init__(coordinator)
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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""

        sensor = self.coordinator.data.get_sensor(
            self._device.id,
            self._sensor.id
        )
        if sensor.value != self._sensor.value:
            _LOGGER.debug(
                f'Сенсор "{self._device.name}_{self._sensor.name}" обновился '
                f'с {self._sensor.value} на {sensor.value}')
        self._sensor.value = sensor.value
        self.async_write_ha_state()


