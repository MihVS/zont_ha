import asyncio
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator
from .const import DOMAIN, BUTTON_ZONT, MANUFACTURER, SWITCH_ZONT
from .core.models_zont import DeviceZONT, CustomControlZONT
from .core.zont import Zont

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    zont: Zont = hass.data[DOMAIN][entry_id]
    coordinator = ZontCoordinator(hass, zont)

    await coordinator.async_config_entry_first_refresh()

    for device in zont.data.devices:
        switch = []
        controls = device.custom_controls
        for control in controls:
            if control.type == SWITCH_ZONT:
                unique_id = f'{entry_id}{device.id}{control.id}'
                switch.append(
                    ZontSwitch(coordinator, device, control, unique_id)
                )
        if switch:
            async_add_entities(switch)
            _LOGGER.debug(f'Добавлены выключатели: {switch}')


class ZontSwitch(CoordinatorEntity, SwitchEntity):

    def __init__(
            self, coordinator: ZontCoordinator, device: DeviceZONT,
            control: CustomControlZONT, unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self.zont: Zont = coordinator.zont
        self._device = device
        self._control = control
        self._unique_id = unique_id

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return self._control.status

    @property
    def name(self) -> str:
        name = self._control.name.get('when_active')
        name = f'{self._device.name}_{name}'
        return name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.id)},
            "name": self._device.name,
            "sw_version": None,
            "model": self._device.model,
            "manufacturer": MANUFACTURER
        }

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Switch entity {self.name}>"
        return super().__repr__()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        _LOGGER.warning('Включил выключатель')
        # await asyncio.sleep(1)
        # await self.zont.get_update()
        # self._handle_coordinator_update()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        _LOGGER.warning('Выключил выключатель')

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""
        # _LOGGER.debug(self.coordinator.data)
        # _LOGGER.warning(self.coordinator.zont)
        self._device: DeviceZONT = self.coordinator.data.get_device(
            self._device.id
        )
        self._control = self.zont.get_custom_control(
            self._device.id, self._control.id
        )

        self.async_write_ha_state()

# как обновлять всё один раз через координатор
