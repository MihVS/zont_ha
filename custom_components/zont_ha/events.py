"""События ZONT в шине Home Assistant.

Каждый webhook от ZONT публикуется как событие `zont_ha_event`. На него
можно повесить автоматизацию напрямую или через триггер устройства
(device_trigger.py) — по разделу `trigger` ниже.
"""
from .core.models_zont_webhook import DeviceEventWebhook

EVENT_ZONT = 'zont_ha_event'

TRIGGER_ANY = 'any_event'

# Триггер устройства -> типы событий ZONT. У старых приборов и Z3K
# одно и то же событие называется по-разному.
TRIGGER_EVENT_TYPES: dict[str, frozenset[str]] = {
    'boiler_failure': frozenset({'BoilerFail', 'OTFail', 'Z3K_OTFail'}),
    'boiler_failure_cleared': frozenset(
        {'BoilerFailCancel', 'OTFailCancel', 'Z3K_OTRestore'}),
    'guard_alarm': frozenset({'Alarm', 'ZoneAlarm', 'Z3K_ZoneAlarm'}),
    'guard_alarm_cleared': frozenset({'ZoneAlarmCancel', 'Z3K_ZoneRestore'}),
    'guard_on': frozenset({'GuardOn', 'Z3K_ZoneGuardOn'}),
    'guard_off': frozenset({'GuardOff', 'Z3K_ZoneGuardOff'}),
    'power_lost': frozenset({'PowerOff', 'MainPowerLost'}),
    'power_restored': frozenset({'PowerOn', 'MainPowerFound'}),
    'connection_lost': frozenset({'disconnected', 'Z3K_LinkLost'}),
    'connection_restored': frozenset(
        {'connected', 'reconnected', 'Z3K_LinkRestored'}),
    'temperature_high': frozenset({'TemperatureHigh', 'Z3K_TemperatureHigh'}),
    'temperature_low': frozenset({'TemperatureLow', 'Z3K_TemperatureLow'}),
    'leakage': frozenset({'Z3K_Leakage'}),
    'smoke': frozenset({'Z3K_SmokeSensor'}),
    'user_alarm': frozenset({'UserAlarm', 'UserEvent'}),
}

TRIGGER_TYPES = (*TRIGGER_EVENT_TYPES, TRIGGER_ANY)


def trigger_for(event_type: str) -> str | None:
    """Триггер устройства для типа события ZONT, None — без триггера."""
    for trigger, event_types in TRIGGER_EVENT_TYPES.items():
        if event_type in event_types:
            return trigger
    return None


def build_event_data(
        event: DeviceEventWebhook, ha_device_id: str | None) -> dict:
    additional_info = event.additional_info
    return {
        'device_id': ha_device_id,
        'zont_device_id': event.device_id,
        'type': event.type,
        'trigger': trigger_for(event.type),
        'title': event.title,
        'details': event.details,
        'important': event.important,
        'source': event.source,
        'time': event.time,
        'object_id': additional_info.object_id if additional_info else None,
    }
