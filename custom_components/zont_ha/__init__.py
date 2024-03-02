import logging
from datetime import timedelta

import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator, UpdateFailed
)
from .const import (
    DOMAIN, PLATFORMS, TIME_UPDATE, MANUFACTURER,
    CONFIGURATION_URL, COUNTER_CONNECT, TIME_OUT_UPDATE_DATA
)
from .core.zont import Zont

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    entry_id = config_entry.entry_id
    email = config_entry.data.get("mail")
    token = config_entry.data.get("token")
    zont = Zont(hass, email, token)
    await zont.get_update(old_api=True)
    coordinator = ZontCoordinator(hass, zont)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(
        config_entry, PLATFORMS
    )
    return True


class ZontCoordinator(DataUpdateCoordinator):
    """Координатор для общего обновления данных"""

    _count_connect: int = 0

    def __init__(self, hass, zont):
        super().__init__(
            hass,
            _LOGGER,
            name="ZONT",
            update_interval=timedelta(seconds=TIME_UPDATE),
        )
        self.zont: Zont = zont

    def devices_info(self, device_id: int):
        device_old = self.zont.get_device_old(device_id)
        device = self.zont.get_device(device_id)
        hardware_type = device_old.hardware_type
        hw_version = None
        if hardware_type is not None:
            hw_version = hardware_type.code
        device_info = DeviceInfo(**{
            "identifiers": {(DOMAIN, device.id)},
            "name": device.name,
            "sw_version": device_old.firmware_version,
            "hw_version": hw_version,
            "serial_number": device_old.serial,
            "configuration_url": CONFIGURATION_URL,
            "model": device.model,
            "manufacturer": MANUFACTURER,
        })
        return device_info

    async def _async_update_data(self):
        """Обновление данных API zont"""
        try:
            async with async_timeout.timeout(TIME_OUT_UPDATE_DATA):
                await self.zont.get_update()
                self._count_connect = 0
                return self.zont
        except Exception as err:
            if self._count_connect < COUNTER_CONNECT:
                self._count_connect += 1
                _LOGGER.warning(
                    f'Неудачная попытка обновления данных ZONT. '
                    f'Осталось попыток: {COUNTER_CONNECT - self._count_connect}'
                )
                return self.zont
            else:
                raise UpdateFailed(f"Ошибка соединения с API zont: {err}")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(entry, platform)
    return True
