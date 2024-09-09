import logging
from functools import cached_property

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from . import ZontCoordinator
from .const import DOMAIN, BINARY_SENSOR_TYPES, SENSOR_TYPE_ICON, UNIT_BY_TYPE
from .core.exceptions import SensorNotFoundError
from .core.models_zont import SensorZONT, DeviceZONT, OTSensorZONT
from .core.utils import get_devise_class_sensor, get_unit_sensor, \
    validate_value_sensor

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
        sens = []
        for sensor in device.sensors:
            unique_id = f'{entry_id}{device.id}{sensor.id}'
            if sensor.type not in BINARY_SENSOR_TYPES:
                sens.append(ZontSensor(coordinator, device, sensor, unique_id))
        for ot_sensor in device.ot_sensors:
            unique_id = f'{entry_id}{device.id}{ot_sensor.id}'
            sens.append(ZontSensor(coordinator, device, ot_sensor, unique_id))
        if sens:
            async_add_entities(sens)
            _LOGGER.debug(f'Добавлены сенсоры: {sens}')


class ZontSensor(CoordinatorEntity, SensorEntity):

    def __init__(
            self, coordinator: ZontCoordinator, device: DeviceZONT,
            sensor: SensorZONT | OTSensorZONT, unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._sensor = sensor
        self._unique_id = unique_id
        self._attr_device_info = coordinator.devices_info(device.id)
        self._attr_icon = SENSOR_TYPE_ICON.get(sensor.type)

    @cached_property
    def state_class(self) -> SensorStateClass | str | None:
        """Return the state class of this entity, if any."""
        if self._sensor.type in UNIT_BY_TYPE:
            return SensorStateClass.MEASUREMENT
        return None

    @cached_property
    def name(self) -> str:
        return f'{self._device.name}_{self._sensor.name}'

    @property
    def native_value(self) -> float | str:
        """Возвращает состояние сенсора"""
        if self._sensor.type == 'battery' and isinstance(self._sensor.value, float):
            return int(self._sensor.value)
        elif isinstance(self._sensor.value, float):
            return round(self._sensor.value, 2)
        else:
            return self._sensor.value

    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        """Возвращает единицу измерения сенсора из API zont"""
        return get_unit_sensor(self._sensor)

    @cached_property
    def unique_id(self) -> str:
        return self._unique_id

    @cached_property
    def device_class(self) -> str | None:
        return get_devise_class_sensor(self._sensor)

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Sensor entity {self.name}>"
        return super().__repr__()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""

        sensor = self.coordinator.data.get_sensor(
            self._device.id,
            self._sensor.id
        )
        if sensor is None:
            _LOGGER.error(f'Сенсор по id={self._sensor.id} не найден')
            raise SensorNotFoundError
        if sensor.value != self._sensor.value:
            _LOGGER.debug(
                f'Сенсор "{self._device.name}_{self._sensor.name}" обновился '
                f'с {self._sensor.value} на {sensor.value}')
        self._sensor.value = validate_value_sensor(
            sensor.value, self._sensor.value)
        self.async_write_ha_state()
