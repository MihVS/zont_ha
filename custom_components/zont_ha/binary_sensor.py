import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass, BinarySensorEntity
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from . import ZontCoordinator
from .const import DOMAIN, MANUFACTURER, BINARY_SENSOR_TYPES
from .core.models_zont import SensorZONT, DeviceZONT
from .core.zont import type_binary_sensor, Zont

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    coordinator = hass.data[DOMAIN][entry_id]
    zont = coordinator.zont

    for device in zont.data.devices:
        binary_sensors = []
        states = device.car_state
        fields = []
        if states:
            fields = states.__fields__.keys()
        for name_state in fields:
            if isinstance(getattr(states, name_state), bool):
                unique_id = f'{entry_id}{device.id}{name_state}'
                binary_sensors.append(CarBinarySensor(
                    coordinator, device, name_state, unique_id
                ))

        for sensor in device.sensors:
            unique_id = f'{entry_id}{device.id}{sensor.id}'
            if sensor.type in BINARY_SENSOR_TYPES:
                binary_sensors.append(ZontBinarySensor(
                    coordinator, device, sensor, unique_id
                ))
        if binary_sensors:
            async_add_entities(binary_sensors)
            _LOGGER.debug(f'Добавлены бинарные сенсоры: {binary_sensors}')


class CarBinarySensor(CoordinatorEntity, BinarySensorEntity):

    def __init__(
            self, coordinator: ZontCoordinator, device: DeviceZONT,
            sensor_name: str, unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._zont: Zont = coordinator.zont
        self._device: DeviceZONT = device
        self._sensor_name: str = sensor_name
        self._unique_id: str = unique_id

    @property
    def name(self) -> str:
        return f'{self._device.name}_{self._sensor_name}'

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return getattr(self._device.car_state, self._sensor_name)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.id)},
            "name": self._device.name,
            "sw_version": None,
            "model": self._device.model,
            "manufacturer": MANUFACTURER,
        }

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Binary sensor entity {self.name}>"
        return super().__repr__()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""

        self._device = self.coordinator.data.get_device(self._device.id)
        self.async_write_ha_state()


class ZontBinarySensor(CoordinatorEntity, BinarySensorEntity):

    def __init__(
            self, coordinator: ZontCoordinator, device: DeviceZONT,
            sensor: SensorZONT, unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._zont: Zont = coordinator.zont
        self._device: DeviceZONT = device
        self._sensor: SensorZONT = sensor
        self._unique_id: str = unique_id

    @property
    def name(self) -> str:
        return f'{self._device.name}_{self._sensor.name}'

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the class of this entity."""
        match self._sensor.type:
            case type_binary_sensor.leakage:
                return BinarySensorDeviceClass.MOISTURE
            case type_binary_sensor.smoke:
                return BinarySensorDeviceClass.SMOKE
            case type_binary_sensor.opening:
                return BinarySensorDeviceClass.DOOR
            case type_binary_sensor.motion:
                return BinarySensorDeviceClass.MOTION
            case _:
                return None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self._zont.is_on_binary(self._device, self._sensor)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.id)},
            "name": self._device.name,
            "sw_version": None,
            "model": self._device.model,
            "manufacturer": MANUFACTURER,
        }

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Binary sensor entity {self.name}>"
        return super().__repr__()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""

        sensor = self.coordinator.data.get_sensor(
            self._device.id,
            self._sensor.id
        )
        self._sensor.value = sensor.value
        self.async_write_ha_state()
