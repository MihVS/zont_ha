import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator
from .const import DOMAIN, SWITCH_ZONT
from .core.models_zont import DeviceZONT, CustomControlZONT
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
        switch = []
        for control in device.custom_controls:
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
        self._zont: Zont = coordinator.zont
        self._device = device
        self._control = control
        self._unique_id = unique_id
        self._attr_device_info = coordinator.devices_info(device.id)

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return self._control.status

    @property
    def name(self) -> str:
        name = self._control.name.get('name')
        return f'{self._device.name}_{name}'

    @property
    def unique_id(self) -> str:
        return self._unique_id

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Switch entity {self.name}>"
        return super().__repr__()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self._zont.toggle_switch(
            device=self._device, control=self._control, command=True
        )
        self._control.status = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self._zont.toggle_switch(
            device=self._device, control=self._control, command=False
        )
        self._control.status = False
        self.async_write_ha_state()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self._control.status:
            await self._zont.toggle_switch(
                device=self._device, control=self._control, command=False
            )
            self._control.status = False
        else:
            await self._zont.toggle_switch(
                device=self._device, control=self._control, command=True
            )
            self._control.status = True
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""
        self._device: DeviceZONT = self._zont.get_device(
            self._device.id
        )
        self._control = self._zont.get_custom_control(
            self._device.id, self._control.id
        )

        self.async_write_ha_state()
