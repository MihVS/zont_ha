import logging

from homeassistant.components.climate import HVACMode, \
    ClimateEntity, PRESET_ECO, PRESET_HOME, PRESET_NONE, HVAC_MODES
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator, DOMAIN
from .const import MANUFACTURER

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

    for device in zont.data.devices:
        thermostat = []
        heating_circuits = device.heating_circuits
        for heating_circuit in heating_circuits:
            unique_id = f'{entry_id}{device.id}{heating_circuit.id}'
            thermostat.append(ZontClimateEntity(
                coordinator, device.id, heating_circuit.id, unique_id)
            )
        async_add_entities(thermostat)
        _LOGGER.debug(f'Добавлены термостаты: {thermostat}')


class ZontClimateEntity(CoordinatorEntity, ClimateEntity):
    """Базовый класс для климата zont"""

    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_max_temp = 80
    _attr_min_temp = 5
    _attr_target_temperature_step = 0.1
    # _attr_preset_modes = ['Лето', 'Чилл', 'none']
    _attr_preset_modes = [PRESET_ECO, PRESET_HOME, PRESET_NONE]
    # _attr_preset_modes = HVAC_MODES
    _attr_preset_mode = PRESET_NONE

    def __init__(
            self, coordinator: ZontCoordinator, device_id: int,
            heating_circuit_id: int, unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._unique_id = unique_id
        self.zont = coordinator.zont
        self._device = self.zont.get_device(device_id)
        self._heating_circuit = self.zont.get_heating_circuit(
            device_id, heating_circuit_id
        )

    # @property
    # def preset_mode(self):
    #     return self._attr_preset_mode
    #
    # @property
    # def preset_modes(self):
    #     return self._attr_preset_modes
    #
    def set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        _LOGGER.warning(f'Установил режим: {preset_mode}')

    @property
    def hvac_mode(self) -> HVACMode | None:
        if self._heating_circuit.is_off:
            return HVACMode.OFF
        return HVACMode.HEAT

    # @property
    # def hvac_modes(self) -> list[HVACMode]:
    #     """Return the list of available hvac operation modes."""
    #     return self._attr_hvac_modes

    @property
    def name(self) -> str:
        name = f'{self._device.name}_{self._heating_circuit.name}'
        return name

    # async def async_set_temperature(self, **kwargs) -> None:
    #     """Set new target temperature."""
    #     pass

    @property
    def temperature_unit(self) -> str:
        return TEMP_CELSIUS

    @property
    def current_temperature(self) -> float:
        return self._heating_circuit.actual_temp

    @property
    def target_temperature(self) -> float:
        return self._heating_circuit.target_temp

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
            "manufacturer": MANUFACTURER,
        }

# Нужно понять как entity_id сделать при создании термостатов.
# Пока получается None
