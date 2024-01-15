import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, BUTTON_ZONT, MANUFACTURER
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

    for device in zont.data.devices:
        buttons = []
        controls = device.custom_controls
        for control in controls:
            if control.type == BUTTON_ZONT:
                unique_id = f'{entry_id}{device.id}{control.id}'
                buttons.append(ZontButton(zont, device, control, unique_id))
        if buttons:
            async_add_entities(buttons)
            _LOGGER.debug(f'Добавлены кнопки: {buttons}')


class ZontButton(ButtonEntity):

    def __init__(
            self, zont: Zont, device: DeviceZONT,
            control: CustomControlZONT, unique_id: str
    ) -> None:
        self._zont = zont
        self._device = device
        self._control = control
        self._unique_id = unique_id

    @property
    def name(self) -> str:
        name = f'{self._device.name}_{self._control.name}'
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

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._zont.toggle_switch(
            device=self._device, control=self._control, command=True
        )
