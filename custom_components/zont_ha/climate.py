import logging

from homeassistant.components.climate import HVACAction, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType

from . import ZontCoordinator, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    entry_id = config_entry.entry_id

    zont = hass.data[DOMAIN][entry_id]
    coordinator = ZontCoordinator(hass, zont)

    await coordinator.async_config_entry_first_refresh()


class ZontClimateEntity(Entity):
    """Базовый класс для климата zont"""

    _attr_current_temperature: float | None = None
    _attr_hvac_action: HVACAction | None = None
    _attr_hvac_mode: HVACMode | None
    _attr_hvac_modes: [HVACMode.HEAT, HVACMode.OFF]
    _attr_is_aux_heat: bool | None
    _attr_max_temp: 30
    _attr_min_temp: 5
    _attr_precision: float
    _attr_preset_mode: str | None
    _attr_preset_modes: list[str] | None
    _attr_target_temperature_step: 0.1
    _attr_target_temperature: float | None = None
    _attr_temperature_unit: str

    def __init__(
            self, coordinator: ZontCoordinator,
            unique_id: str
    ) -> None:
        super().__init__(coordinator)

