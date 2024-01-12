import logging

from homeassistant.components.climate import (
    HVACMode, ClimateEntity, ClimateEntityFeature, HVACAction, PRESET_NONE
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator, DOMAIN
from .const import MANUFACTURER
from .core.models_zont import DeviceZONT, AccountZont, HeatingModeZONT
from .core.zont import Zont

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
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
    _attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.PRESET_MODE
    )

    def __init__(
            self, coordinator: ZontCoordinator, device_id: int,
            heating_circuit_id: int, unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._unique_id: str = unique_id
        self.zont: Zont = coordinator.zont
        self._device: DeviceZONT = self.zont.get_device(device_id)
        self._heating_circuit = self.zont.get_heating_circuit(
            device_id, heating_circuit_id
        )
        self._heating_modes: list[HeatingModeZONT] = self._device.heating_modes
        self._attr_min_temp, self._attr_max_temp = (
            self.zont.get_min_max_values_temp(self._heating_circuit.name))

    @property
    def preset_modes(self) -> list[str] | None:
        _preset_modes = self.zont.get_names_get_heating_mode(
            self._heating_modes
        )
        _preset_modes.append(PRESET_NONE)
        return _preset_modes

    @property
    def preset_mode(self) -> str | None:
        id_heating_mode = self._heating_circuit.current_mode
        heating_mode = self.zont.get_heating_mode(
            self._device.id, id_heating_mode
        )
        if heating_mode is not None:
            return heating_mode.name
        return PRESET_NONE

    def set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        self._attr_preset_mode = preset_mode
        _LOGGER.warning(f'Установил режим: {preset_mode}')

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, cool mode."""
        if self._heating_circuit.is_off:
            return HVACMode.OFF
        return HVACMode.HEAT

    # @property
    # def hvac_modes(self) -> list[HVACMode]:
    #     """Return the list of available hvac operation modes."""
    #     return self._attr_hvac_modes

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation if supported."""
        if self._heating_circuit.active:
            return HVACAction.HEATING
        return HVACAction.OFF

    @property
    def name(self) -> str:
        return f'{self._device.name}_{self._heating_circuit.name}'

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

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Climate entity {self.name}>"

        return super().__repr__()

# Нужно добавить обновление параметров в климате
# Добавить функционал упраления заданной температуры
# Научиться изменять HVAC режим
# Научиться изменять preset
