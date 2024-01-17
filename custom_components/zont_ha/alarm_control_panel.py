import asyncio
import logging

from homeassistant.components.alarm_control_panel import \
    AlarmControlPanelEntity, AlarmControlPanelEntityFeature
from homeassistant.components.climate import (
    HVACMode, ClimateEntity, ClimateEntityFeature, HVACAction, PRESET_NONE
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator, DOMAIN
from .const import MANUFACTURER
from .core.exceptions import TemperatureOutOfRangeError, SetHvacModeError
from .core.models_zont import DeviceZONT, HeatingModeZONT
from .core.zont import Zont

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    coordinator = hass.data[DOMAIN][entry_id]
    zont: Zont = coordinator.zont

    for device in zont.data.devices:
        alarms = []
        guard_zones = device.guard_zones
        for guard_zone in guard_zones:
            unique_id = f'{entry_id}{device.id}{guard_zone.id}'
            alarms.append(ZontAlarm(
                coordinator, device.id, guard_zone.id, unique_id)
            )
        if alarms:
            async_add_entities(alarms)
            _LOGGER.debug(f'Добавлены охранные зоны: {alarms}')


class ZontAlarm(CoordinatorEntity, AlarmControlPanelEntity):

    _attr_code_format = None
    # _attr_changed_by = 'pending'
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_AWAY |
        AlarmControlPanelEntityFeature.TRIGGER
    )

    def __init__(
            self, coordinator: ZontCoordinator, device_id: int,
            guard_zone_id: int, unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._guard_zone_id = guard_zone_id
        self._unique_id = unique_id
        self.zont: Zont = coordinator.zont
        self._device: DeviceZONT = self.zont.get_device(device_id)
        self._guard_zone = self.zont.get_guard_zone(
            device_id, guard_zone_id
        )

    @property
    def name(self) -> str:
        return f'{self._device.name}_{self._guard_zone.name}'

    @property
    def state(self) -> StateType:
        """Return the state of the entity."""
        return 'arming'

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def supported_features(self) -> AlarmControlPanelEntityFeature:
        """Return the list of supported features."""
        return self._attr_supported_features

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
            return f"<Alarm entity {self.name}>"
        return super().__repr__()

