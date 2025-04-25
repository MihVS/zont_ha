import logging
from functools import cached_property

from homeassistant.components.device_tracker import TrackerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator
from .const import DOMAIN, ENTRIES, CURRENT_ENTITY_IDS
from .core.models_zont import DeviceZONT
from .core.models_zont_old import DeviceZontOld
from .core.zont import Zont

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    coordinator = hass.data[DOMAIN][ENTRIES][entry_id]
    zont = coordinator.zont

    for device in zont.data.devices:
        states = device.car_state
        device_old: DeviceZontOld = zont.get_device_old(device.id)
        stationary_location = device_old.stationary_location
        widget_type = device_old.widget_type
        if stationary_location and widget_type != 'ztc':
            unique_id = f'{entry_id}{device.id}{device_old.serial}'
            device_tracker = StationaryPosition(coordinator, device, unique_id)
            async_add_entities([device_tracker])
            hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
                device_tracker.unique_id)
            _LOGGER.debug(
                f'Добавлено устройство отслеживания: {device_tracker}'
            )

        if states:
            unique_id = f'{entry_id}{device.id}{device_old.serial}'
            device_tracker = CarPosition(coordinator, device, unique_id)
            async_add_entities([device_tracker])
            hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
                device_tracker.unique_id)
            _LOGGER.debug(
                f'Добавлено устройство отслеживания: {device_tracker}'
            )


class Position(CoordinatorEntity, TrackerEntity):

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
        return f'{self._device.name}_device_tracker'

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        raise NotImplementedError()

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        raise NotImplementedError()

    @property
    def source_type(self) -> SourceType | str:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Device tracker entity {self.name}>"
        return super().__repr__()


class CarPosition(Position):

    @property
    def location_name(self) -> str | None:
        """Return a location name for the current location of the device."""
        return self._device.car_state.address

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self._device.car_state.position.y

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self._device.car_state.position.x

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""
        self._device = self.coordinator.data.get_device(self._device.id)
        self.async_write_ha_state()


class StationaryPosition(Position):

    def __init__(
            self, coordinator: ZontCoordinator, device: DeviceZONT,
            unique_id: str
    ) -> None:
        super().__init__(coordinator, device, unique_id)
        self._device_old: DeviceZontOld = self._zont.get_device_old(device.id)
        self._unique_id = unique_id

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self._device_old.stationary_location.latitude

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self._device_old.stationary_location.longitude

    @cached_property
    def unique_id(self) -> str:
        return self._unique_id
