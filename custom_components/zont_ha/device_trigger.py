"""Триггеры устройства по событиям ZONT."""
import voluptuous as vol

from homeassistant.components.device_automation import (
    DEVICE_TRIGGER_BASE_SCHEMA,
)
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .events import EVENT_ZONT, TRIGGER_ANY, TRIGGER_TYPES

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES)}
)


async def async_get_triggers(
        hass: HomeAssistant, device_id: str) -> list[dict]:
    device = dr.async_get(hass).async_get(device_id)
    if device is None or not any(
            domain == DOMAIN for domain, _ in device.identifiers):
        return []
    return [
        {
            CONF_PLATFORM: 'device',
            CONF_DOMAIN: DOMAIN,
            CONF_DEVICE_ID: device_id,
            CONF_TYPE: trigger_type,
        }
        for trigger_type in TRIGGER_TYPES
    ]


async def async_attach_trigger(
        hass: HomeAssistant,
        config: ConfigType,
        action: TriggerActionType,
        trigger_info: TriggerInfo) -> CALLBACK_TYPE:
    event_data = {CONF_DEVICE_ID: config[CONF_DEVICE_ID]}
    if config[CONF_TYPE] != TRIGGER_ANY:
        event_data['trigger'] = config[CONF_TYPE]
    event_config = event_trigger.TRIGGER_SCHEMA({
        event_trigger.CONF_PLATFORM: 'event',
        event_trigger.CONF_EVENT_TYPE: EVENT_ZONT,
        event_trigger.CONF_EVENT_DATA: event_data,
    })
    return await event_trigger.async_attach_trigger(
        hass, event_config, action, trigger_info, platform_type='device'
    )
