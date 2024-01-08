import logging

from homeassistant.components.climate import HVACAction, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
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


class ZontClimateEntity(CoordinatorEntity, Entity):
    """Базовый класс для климата zont"""

    # _attr_current_temperature: float | None = None
    # _attr_hvac_action: HVACAction | None = None
    # _attr_hvac_mode: HVACMode | None
    _attr_hvac_modes: [HVACMode.HEAT, HVACMode.OFF]
    _attr_is_aux_heat: bool | None
    _attr_max_temp: 30
    _attr_min_temp: 5
    _attr_precision: float
    _attr_preset_mode: str | None
    _attr_preset_modes: list[str] | None
    _attr_target_temperature_step: 0.1
    # _attr_target_temperature: float | None = None
    _attr_temperature_unit: str

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

    @property
    def name(self) -> str:
        name = f'{self._device.name}_{self._heating_circuit.name}'
        return name

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        pass

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
