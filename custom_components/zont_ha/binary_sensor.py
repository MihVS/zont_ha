import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass, BinarySensorEntity
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator
from .const import (
    DOMAIN, CURRENT_ENTITY_IDS, ENTRIES
)
from .core.models_zont_v3 import (SensorZONT, DeviceZONT, StatusZONT)
from .core.utils import is_binary_sensor
from .core.zont import type_binary_sensor, Zont

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    coordinator = hass.data[DOMAIN][ENTRIES][entry_id]
    zont: DeviceZONT = coordinator.zont

    for device in zont.data.devices:
        binary_sensors = []
        for sensor in device.sensors:
            unique_id = f'{entry_id}{device.id}{sensor.id}'
            if is_binary_sensor(sensor):
                binary_sensors.append(ZontBinarySensor(
                    coordinator, device, sensor, unique_id
                ))
        if device.controls:
            for control_status in device.controls.statuses:
                unique_id = f'{entry_id}{device.id}{control_status.id}'
                binary_sensors.append(ZontBinarySensorControl(
                    coordinator, device, control_status, unique_id))
        binary_sensors.append(ZontOnlineBinarySensor(
            coordinator, device, unique_id=f'{entry_id}{device.id}_online'
        ))
        for binary_sensor in binary_sensors:
            hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
                binary_sensor.unique_id)
        if binary_sensors:
            async_add_entities(binary_sensors)
            _LOGGER.debug(f'Добавлены бинарные сенсоры: {binary_sensors}')


class ZontOnlineBinarySensor(CoordinatorEntity, BinarySensorEntity):

    def __init__(
            self, coordinator: ZontCoordinator, device: DeviceZONT,
            unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._zont: Zont = coordinator.zont
        self._device: DeviceZONT = device
        self._unique_id: str = unique_id
        self._attr_device_info = coordinator.devices_info(device.id)

    @property
    def name(self) -> str:
        return f'{self._device.name}_online'

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the class of this entity."""
        return BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self._device.online

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Binary sensor entity {self.name}>"
        return super().__repr__()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""

        device = self.coordinator.zont.get_device(self._device.id)
        if device.online != self._device.online:
            _LOGGER.debug(
                f'Состояние устройства "{self._device.name}" '
                f'обновилось с {self._device.online} на {device.online}')
        self._device.online = device.online
        if not device.online:
            _LOGGER.warning(f'Устройство {self._device.name} недоступно!')
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
        self._attr_device_info = coordinator.devices_info(device.id)

    @property
    def name(self) -> str:
        return f'{self._device.name}_{self._sensor.name}'

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the class of this entity."""
        match self._sensor.type.value:
            case type_binary_sensor.leakage:
                return BinarySensorDeviceClass.MOISTURE
            case type_binary_sensor.smoke:
                return BinarySensorDeviceClass.SMOKE
            case type_binary_sensor.opening:
                return BinarySensorDeviceClass.DOOR
            case type_binary_sensor.motion:
                return BinarySensorDeviceClass.MOTION
            case type_binary_sensor.boiler_failure:
                return BinarySensorDeviceClass.PROBLEM
            case type_binary_sensor.room_thermostat:
                return BinarySensorDeviceClass.HEAT
            case _:
                return None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self._sensor.triggered

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Binary sensor entity {self.name}>"
        return super().__repr__()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""

        sensor = self.coordinator.zont.get_sensor(
            self._device.id,
            self._sensor.id
        )
        if sensor.triggered != self._sensor.triggered:
            _LOGGER.debug(
                f'Бинарный сенсор "{self._device.name}_{self._sensor.name}" '
                f'обновился с {self._sensor.triggered} на {sensor.triggered}')
        self._sensor.triggered = sensor.triggered
        self.async_write_ha_state()


class ZontBinarySensorControl(CoordinatorEntity, BinarySensorEntity):

    def __init__(
            self, coordinator: ZontCoordinator, device: DeviceZONT,
            status_control: StatusZONT, unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._zont: Zont = coordinator.zont
        self._device: DeviceZONT = device
        self._status_control: StatusZONT = status_control
        self._unique_id: str = unique_id
        self._attr_device_info = coordinator.devices_info(device.id)

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Binary sensor entity {self.name}>"
        return super().__repr__()

    @property
    def name(self) -> str:
        name_status_control = self._status_control.name.name
        return f'{self._device.name}_{name_status_control}'

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self._status_control.active

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""

        status_control: StatusZONT = (
            self.coordinator.zont.get_status_control(
                self._device.id, self._status_control.id)
        )
        if status_control.active != self._status_control.active:
            _LOGGER.debug(
                f'Бинарный сенсор "'
                f'{self._device.name}_{self._status_control.name}" '
                f'обновился с '
                f'{self._status_control.active} на {status_control.active}')
        self._status_control.active = status_control.active
        self.async_write_ha_state()
