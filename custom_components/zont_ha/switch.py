import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator
from .const import DOMAIN, ENTRIES, CURRENT_ENTITY_IDS
from .core.models_zont_v3 import DeviceZONT, ToggleButtonsZONT
from .core.zont import Zont

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
        switches = []
        if device.controls:
            for toggle_button in device.controls.toggle_buttons:
                unique_id = f'{entry_id}{device.id}{toggle_button.id}'
                switches.append(
                    ZontSwitch(coordinator, device, toggle_button, unique_id)
                )
        for switch in switches:
            hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
                switch.unique_id)
        if switches:
            async_add_entities(switches)
            _LOGGER.debug(f'Добавлены выключатели: {switches}')


class ZontSwitch(CoordinatorEntity, SwitchEntity):

    def __init__(
            self, coordinator: ZontCoordinator, device: DeviceZONT,
            toggle_button: ToggleButtonsZONT, unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._zont: Zont = coordinator.zont
        self._device = device
        self._toggle_button = toggle_button
        self._unique_id = unique_id
        self._attr_device_info = coordinator.devices_info(device.id)

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Switch entity {self.name}>"
        return super().__repr__()

    @property
    def name(self) -> str:
        return self._toggle_button.name.name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return self._toggle_button.active

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self._zont.switch_button(
            device=self._device,
            button=self._toggle_button,
            command=True
        )
        self._toggle_button.active = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self._zont.switch_button(
            device=self._device,
            button=self._toggle_button,
            command=False
        )
        self._toggle_button.active = False
        self.async_write_ha_state()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self._toggle_button.active:
            await self.async_turn_on()
        else:
            await self.async_turn_off()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""
        toggle_button: ToggleButtonsZONT = self.coordinator.zont.get_toggle_button(
            device_id=self._device.id, toggle_button_id=self._toggle_button.id
        )
        if toggle_button.active != self._toggle_button.active:
            _LOGGER.debug(
                f'Переключатель "'
                f'{self._device.name}_{self._toggle_button.name.name}" '
                f'изменил состояние с '
                f'{self._toggle_button.active} на {toggle_button.active}')
        self._toggle_button.active = toggle_button.active
        self.async_write_ha_state()
