import logging

from homeassistant.components.device_tracker import TrackerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator
from .const import DOMAIN
from .core.models_zont import DeviceZONT
from .core.zont import Zont

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
        states = device.car_state
        if states:
            unique_id = f'{entry_id}{device.id}{"position"}'
            device_tracker = CarPosition(coordinator, device, unique_id)
            async_add_entities([device_tracker])
            _LOGGER.debug(
                f'Добавлено устройство отслеживания: {device_tracker}'
            )


class CarPosition(CoordinatorEntity, TrackerEntity):

    def __init__(
            self, coordinator: ZontCoordinator, device: DeviceZONT,
            unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._zont: Zont = coordinator.zont
        self._device: DeviceZONT = device
        self._unique_id: str = unique_id

    @property
    def name(self) -> str:
        return f'{self._device.name}_device_tracker'

    @property
    def unique_id(self) -> str:
        return self._unique_id

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

    @property
    def source_type(self) -> SourceType | str:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""

        self._device = self.coordinator.data.get_device(self._device.id)
        self.async_write_ha_state()
