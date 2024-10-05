import asyncio
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator
from .const import DOMAIN, BUTTON_ZONT, MANUFACTURER, TIME_OUT_REQUEST
from .core.models_zont import DeviceZONT, CustomControlZONT, HeatingModeZONT
from .core.utils import get_icon
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
        buttons = []
        for control in device.custom_controls:
            if control.type == BUTTON_ZONT:
                unique_id = f'{entry_id}{device.id}{control.id}'
                buttons.append(ZontControlButton(
                    coordinator, zont, device, control, unique_id
                ))
        if buttons:
            async_add_entities(buttons)
            _LOGGER.debug(f'Добавлены кнопки: {buttons}')

        mode_buttons = []
        for mode in device.heating_modes:
            unique_id = f'{entry_id}{device.id}{mode.id}_button'
            mode_buttons.append(HeatingModeButton(
                coordinator, zont, device, mode, unique_id, get_icon(mode.name)
            ))
        if mode_buttons:
            async_add_entities(mode_buttons)
            _LOGGER.debug(f'Добавлены кнопки: {mode_buttons}')


class ButtonZont(CoordinatorEntity, ButtonEntity):

    def __init__(
            self, coordinator: ZontCoordinator, zont: Zont,
            device: DeviceZONT, unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._zont = zont
        self._device = device
        self._unique_id = unique_id

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.id)},
            "name": self._device.name,
            "model": self._device.model,
            "manufacturer": MANUFACTURER
        }

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Button entity {self.name}>"
        return super().__repr__()


class HeatingModeButton(ButtonZont):

    def __init__(
            self, coordinator: ZontCoordinator, zont: Zont, device: DeviceZONT,
            heating_mode: HeatingModeZONT, unique_id: str, icon: str
    ) -> None:
        super().__init__(coordinator, zont, device, unique_id)
        self._heating_mode = heating_mode
        self._attr_icon = icon

    @property
    def name(self) -> str:
        return f'{self._device.name}_{self._heating_mode.name}'

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._zont.set_heating_mode_all_circuit(
            device=self._device, heating_mode_id=self._heating_mode.id
        )
        await asyncio.sleep(TIME_OUT_REQUEST)
        await self.coordinator.async_config_entry_first_refresh()


class ZontControlButton(ButtonZont):

    def __init__(
            self, coordinator: ZontCoordinator, zont: Zont, device: DeviceZONT,
            control: CustomControlZONT, unique_id: str
    ) -> None:
        super().__init__(coordinator, zont, device, unique_id)
        self._control = control

    @property
    def name(self) -> str:
        return f'{self._device.name}_{self._control.name}'

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._zont.toggle_switch(
            device=self._device, control=self._control, command=True
        )
        await asyncio.sleep(TIME_OUT_REQUEST)
        await self.coordinator.async_config_entry_first_refresh()
