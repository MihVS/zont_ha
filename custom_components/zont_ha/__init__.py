import asyncio
import json
import logging
from datetime import timedelta

import async_timeout

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity_registry import async_get
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator, UpdateFailed
)
from .const import (
    DOMAIN, PLATFORMS, TIME_UPDATE, MANUFACTURER, COUNTER_CONNECT,
    TIME_OUT_UPDATE_DATA, ENTRIES, CURRENT_ENTITY_IDS
)
from .core.models_zont_v3 import DeviceZONT
from .core.models_zont_webhook import DeviceEventWebhook, EventZONT
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
        _LOGGER.info(f'Outdated entity deleted {entity_id}')


async def remove_devices(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        selected_devices: list | None):
    """Удаляет неактуальные устройства."""
    _LOGGER.debug(f'Try remove no selected devices. '
                  f'Current devices: {selected_devices}')
    device_reg = dr.async_get(hass)
    all_devices = dr.async_entries_for_config_entry(device_reg,
                                                    config_entry.entry_id)
    if not selected_devices:
        _LOGGER.debug(f'There are no selected devices: {selected_devices}')
        return
    for device in all_devices:
        _LOGGER.debug(f'device identifiers: {device.identifiers}')
        device_id = str(list(device.identifiers)[0][1])
        if not device_id in selected_devices:
            device_reg.async_remove_device(device.id)
            _LOGGER.info(f"Device is removed: {device.name} ({device_id})")


def register_webhook(
        hass: HomeAssistant,
        entry_id: str,
        email: str,
        selected_devices: list[str]):
    """Регистрация webhook в Home Assistant."""
    name_email = ''.join(email.split('@'))
    webhook_id = ''.join(name_email.split('.'))

    webhook.async_unregister(hass, webhook_id)

    webhook.async_register(
        hass,
        DOMAIN,
        f'ZONT Webhook {webhook_id}',
        webhook_id,
        lambda hass, webhook_id, request: handle_webhook(
            hass, webhook_id, request, entry_id, selected_devices),
        allowed_methods=['POST']
    )

    _LOGGER.debug(f'✅ ZONT webhook registered with ID: {webhook_id}')
    webhooks_after = hass.data.get('webhook', {})
    registered = list(webhooks_after.keys()) if webhooks_after else 'None'
    _LOGGER.debug(f'Webhooks after registration: {registered}')


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    _LOGGER.debug('async_setup_entry start')
    config_entry.async_on_unload(
        config_entry.add_update_listener(update_listener)
    )
    entry_id = config_entry.entry_id
    email = config_entry.data.get('mail')
    token = config_entry.data.get('token')
    selected_devices = config_entry.data.get('devices_selected')
    zont = Zont(hass, email, token, selected_devices)
    _LOGGER.debug(f'selected devices: {selected_devices}')

    await remove_devices(hass, config_entry, selected_devices)

    await zont.init_old_data()
    coordinator = ZontCoordinator(hass, zont)
    await coordinator.async_config_entry_first_refresh()
    if getattr(zont, 'data', None) is None:
        # Координатор глотает первые COUNTER_CONNECT отказов и возвращает
        # объект без данных, поэтому first_refresh проходит даже когда API
        # ZONT не ответил. Дальше платформы падают на zont.data.devices, а
        # чистка реестра сносит все сущности аккаунта. Отдаём HA штатный
        # ConfigEntryNotReady: он повторит настройку сам.
        raise ConfigEntryNotReady(
            'ZONT не отдал данные при первом опросе, откладываем настройку'
        )
    _LOGGER.debug(f'config entry data: {config_entry.data}')

    register_webhook(hass, entry_id, email, selected_devices)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(ENTRIES, {})
    hass.data[DOMAIN].setdefault(CURRENT_ENTITY_IDS, {})
    hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id] = []
    hass.data[DOMAIN][ENTRIES][entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        config_entry, PLATFORMS
    )
    current_entries_id = hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id]
    if current_entries_id:
        remove_entity(hass, current_entries_id, config_entry)
    else:
        # Пустой список значит, что ни одна платформа не поднялась.
        # Это отказ опроса, а не исчезновение устройств: чистить реестр
        # в этом случае нельзя, иначе теряются все сущности аккаунта.
        _LOGGER.warning(
            'Список актуальных сущностей пуст, очистка реестра пропущена'
        )
    _LOGGER.debug(f'The unique ID of the current account entities {zont.mail}:'
                  f' {current_entries_id}')
    _LOGGER.debug(f'Number of relevant entities: '
                  f'{len(current_entries_id)}')
    return True

async def handle_webhook(
        hass, webhook_id, request, entry_id, selected_devices):
    """Обрабатываем входящие webhook от ZONT."""
    coordinator = hass.data[DOMAIN][ENTRIES][entry_id]

    body = await request.text()
    try:
        data_json = json.loads(body)
        event_zont = EventZONT.model_validate(data_json)
        data = event_zont.event
        device_id = data.device_id

        if str(device_id) in selected_devices:
            pretty_json = json.dumps(data_json, ensure_ascii=False, indent=2,
                                     sort_keys=True)
            _LOGGER.debug(f'📨 Received webhook request. '
                          f'Webhook id: {webhook_id}. '
                          f'Device id: {webhook_id}. '
                          f'Body: {pretty_json}')
            if coordinator.delayed_refresh_task:
                coordinator.delayed_refresh_task.cancel()
            _LOGGER.debug('Create task for refresh')
            coordinator.delayed_refresh_task = hass.async_create_task(
                coordinator.delayed_refresh()
            )
    except ValueError:
        _LOGGER.warning(f'Wrong webhook request. Webhook id: {webhook_id}. '
                        f'Body: {body}')


async def update_listener(hass, entry):
    """Вызывается при изменении настроек интеграции."""
    _LOGGER.info(f'Restarting integration for entry_id: {entry.entry_id})')
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.info(f'Unloading the zont_ha integration: {entry.entry_id}')
    try:
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, PLATFORMS
        )
        hass.data[DOMAIN][ENTRIES].pop(entry.entry_id)

        return unload_ok
    except Exception as e:
        _LOGGER.error(f'Error uploading the integration: {e}')
        return False


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
        self.delayed_refresh_task: asyncio.Task | None = None

    def devices_info(self, device_id: int):
        device: DeviceZONT = self.zont.get_device(device_id)
        device_info = DeviceInfo(**{
            "identifiers": {(DOMAIN, device.id)},
            "name": device.name,
            "sw_version": device.device_info.version.software,
            "hw_version": device.device_info.version.hardware,
            "serial_number": device.device_info.serial,
            "configuration_url": self.zont.manager._last_base_url,
            "model": device.device_info.model,
            "manufacturer": MANUFACTURER,
        })
        return device_info

    async def delayed_refresh(self):
        try:
            for i in range(3):
                _LOGGER.debug(f'Resync data. Attempt - {i}')
                await self.async_request_refresh()
                if i < 2:
                    await asyncio.sleep(6)

        except asyncio.CancelledError:
            _LOGGER.debug('Delayed refresh cancelled')
            raise
        finally:
            _LOGGER.debug('Delayed refresh stopped')
            if asyncio.current_task() is self.delayed_refresh_task:
                self.delayed_refresh_task = None

    async def _async_update_data(self):
        """Обновление данных API zont"""
        _LOGGER.debug('Start updating the data...')
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


async def async_migrate_entry(hass, config_entry):
    """Миграция с версии 2 на 3."""
    if config_entry.version == 2:
        hass.config_entries.async_update_entry(
            config_entry,
            version=3
        )
        _LOGGER.info('Миграция с версии 2 на 3 выполнена (нулевая миграция)')
    return True
