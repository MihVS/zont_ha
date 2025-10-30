import logging
from datetime import timedelta

import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_registry import async_get
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator, UpdateFailed
)
from .const import (
    DOMAIN, PLATFORMS, TIME_UPDATE, MANUFACTURER,
    CONFIGURATION_URL, COUNTER_CONNECT, TIME_OUT_UPDATE_DATA, ENTRIES,
    CURRENT_ENTITY_IDS
)
from .core.models_zont_v3 import DeviceZONT
from .core.zont import Zont

_LOGGER = logging.getLogger(__name__)


def remove_entity(hass: HomeAssistant, current_entries_id: list,
                  config_entry: ConfigEntry):
    """Удаление неиспользуемых сущностей"""
    entity_registry = async_get(hass)
    remove_entities = []
    for entity_id, entity in entity_registry.entities.items():
        if entity.config_entry_id == config_entry.entry_id:
            if entity.unique_id not in current_entries_id:
                remove_entities.append(entity_id)
    for entity_id in remove_entities:
        entity_registry.async_remove(entity_id)
        _LOGGER.info(f'Удалена устаревшая сущность {entity_id}')


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    entry_id = config_entry.entry_id
    email = config_entry.data.get('mail')
    token = config_entry.data.get('token')
    selected_devices = config_entry.data.get('devices_selected')
    zont = Zont(hass, email, token, selected_devices)
    # await zont.get_update(old_api=True)
    coordinator = ZontCoordinator(hass, zont)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(ENTRIES, {})
    hass.data[DOMAIN].setdefault(CURRENT_ENTITY_IDS, {})
    hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id] = []
    hass.data[DOMAIN][ENTRIES][entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        config_entry, PLATFORMS
    )
    current_entries_id = hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id]
    remove_entity(hass, current_entries_id, config_entry)
    _LOGGER.debug(f'Unique_id актуальных сущностей аккаунта {zont.mail}: '
                  f'{current_entries_id}')
    _LOGGER.debug(f'Количество актуальных сущностей: '
                  f'{len(current_entries_id)}')
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
        device: DeviceZONT = self.zont.get_device(device_id)
        device_info = DeviceInfo(**{
            "identifiers": {(DOMAIN, device.id)},
            "name": device.name,
            "sw_version": device.device_info.version.software,
            "hw_version": device.device_info.version.hardware,
            "serial_number": device.device_info.serial,
            "configuration_url": CONFIGURATION_URL,
            "model": device.device_info.model,
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
                _LOGGER.warning(err)
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
