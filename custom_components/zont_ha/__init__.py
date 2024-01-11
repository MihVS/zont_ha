import logging
from datetime import timedelta

import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator, UpdateFailed
)
from .const import DOMAIN
from .core.zont import Zont

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    # _LOGGER.warning(f'Настройка: {config_entry.unique_id}')
    # _LOGGER.warning(f'Смотрим параметры: {config_entry}')
    entry_id = config_entry.entry_id
    email = config_entry.data.get("mail")
    token = config_entry.data.get("token")
    zont = Zont(hass, email, token)
    await zont.get_update()

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry_id] = zont
    await hass.config_entries.async_forward_entry_setups(
        config_entry, ['sensor', 'climate']
    )
    return True


class ZontCoordinator(DataUpdateCoordinator):
    """Координатор для общего обновления данных"""

    def __init__(self, hass, zont):
        super().__init__(
            hass,
            _LOGGER,
            name="ZONT",
            update_interval=timedelta(seconds=60),
        )
        self.zont = zont

    async def _async_update_data(self):
        """Обновление данных API zont"""
        try:
            async with async_timeout.timeout(10):
                await self.zont.get_update()
                return self.zont

        except Exception as err:
            raise UpdateFailed(f"Ошибка соединения с API zont: {err}")
