import asyncio
import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity, AlarmControlPanelEntityFeature,
    AlarmControlPanelState
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator, DOMAIN
from .const import (
    COUNTER_REPEAT, TIME_OUT_REPEAT, TIME_OUT_REQUEST, CURRENT_ENTITY_IDS,
    ENTRIES
)
from .core.models_zont import DeviceZONT
from .core.zont import Zont

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    coordinator = hass.data[DOMAIN][ENTRIES][entry_id]
    zont: Zont = coordinator.zont
    for device in zont.data.devices:
        alarms = []
        for guard_zone in device.guard_zones:
            unique_id = f'{entry_id}{device.id}{guard_zone.id}'
            alarms.append(ZontAlarm(
                coordinator, device.id, guard_zone.id, unique_id)
            )
        for alarm in alarms:
            hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
                alarm.unique_id)
        if alarms:
            async_add_entities(alarms)
            _LOGGER.debug(f'Добавлены охранные зоны: {alarms}')


class ZontAlarm(CoordinatorEntity, AlarmControlPanelEntity):

    _attr_code_format = None
    _attr_code_arm_required = False
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
        self._zont: Zont = coordinator.zont
        self._device: DeviceZONT = self._zont.get_device(device_id)
        self._guard_zone = self._zont.get_guard_zone(
            self._device, guard_zone_id
        )
        self._attr_device_info = coordinator.devices_info(device_id)

    @property
    def name(self) -> str:
        return f'{self._device.name}_{self._guard_zone.name}'

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        return self._zont.get_state_guard_zone_for_ha(self._guard_zone)

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def supported_features(self) -> AlarmControlPanelEntityFeature:
        """Return the list of supported features."""
        return self._attr_supported_features

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Alarm entity {self.name}>"
        return super().__repr__()

    async def _repeat_check_state(self):
        """
        Обновляем статус охранной зоны пока не получим стабильное
        состояние охранной зоны (под охраной или снято с охраны)
        """
        counter = COUNTER_REPEAT
        while self._zont.need_repeat_update(
                self._guard_zone.state) and counter > 0:
            counter -= 1
            await self.coordinator.async_request_refresh()
            _LOGGER.debug(f'Обновляю статус охраны ещё {counter} раз.')
            await asyncio.sleep(TIME_OUT_REPEAT)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self._zont.toggle_alarm(
            device=self._device, guard_zone=self._guard_zone, command=False
        )
        await asyncio.sleep(TIME_OUT_REQUEST)
        await self.coordinator.async_request_refresh()
        await self._repeat_check_state()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self._zont.toggle_alarm(
            device=self._device, guard_zone=self._guard_zone, command=True
        )
        await asyncio.sleep(TIME_OUT_REQUEST)
        await self.coordinator.async_request_refresh()
        await self._repeat_check_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""
        self._device: DeviceZONT = self.coordinator.zont.get_device(
            self._device_id
        )
        self._guard_zone = self._zont.get_guard_zone(
            self._device, self._guard_zone_id
        )
        self.async_write_ha_state()
