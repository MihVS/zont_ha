import asyncio
import logging

from homeassistant.components.climate import (
    HVACMode, ClimateEntity, ClimateEntityFeature, HVACAction, PRESET_NONE
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator, DOMAIN
from .const import (
    TIME_OUT_REQUEST, MAX_TEMP_AIR, MIN_TEMP_AIR, MODELS_THERMOSTAT_ZONT,
    ENTRIES, CURRENT_ENTITY_IDS, HVAC_OFF_TEMP
)
from .core.enums import TypeOfCircuit
from .core.exceptions import TemperatureOutOfRangeError
from .core.models_zont_v1 import DeviceZontOld
from .core.models_zont_v3 import CircuitZONT, DeviceZONT, HeatingModeZONT
from .core.zont import Zont

_LOGGER = logging.getLogger(__name__)

_OFF_MODE_KEYWORDS = ('выкл', 'откл', 'off')


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    coordinator = hass.data[DOMAIN][ENTRIES][entry_id]
    zont: Zont = coordinator.zont
    for device in zont.data.devices:
        thermostats = []
        circuits: list[CircuitZONT] = device.circuits
        for circuit in circuits:
            if circuit.type in (TypeOfCircuit.CONSUMER, TypeOfCircuit.DHW):
                unique_id = f'{entry_id}{device.id}{circuit.id}'
                thermostats.append(ZontClimateEntity(
                    coordinator, device, circuit, unique_id)
                )
        for thermostat in thermostats:
            hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
                thermostat.unique_id)
        if thermostats:
            async_add_entities(thermostats)
            _LOGGER.debug(f'Добавлены термостаты: {thermostats}')


class ZontClimateEntity(CoordinatorEntity, ClimateEntity):
    """Базовый класс для климата zont"""

    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_max_temp = MAX_TEMP_AIR
    _attr_min_temp = MIN_TEMP_AIR
    _attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.PRESET_MODE |
            ClimateEntityFeature.TURN_ON |
            ClimateEntityFeature.TURN_OFF
    )
    _enable_turn_on_off_backwards_compatibility: bool = False

    def __init__(
            self, coordinator: ZontCoordinator, device: DeviceZONT,
            circuit: CircuitZONT, unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._circuit = circuit
        self._unique_id = unique_id
        self._zont = coordinator.zont
        self._device_old: DeviceZontOld = self._zont.get_device_old(device.id)
        self._attr_target_temperature_step = self._device_old.tempstep
        self._attr_min_temp, self._attr_max_temp = (
            self._zont.get_min_max_values_temp(self._circuit))
        self._attr_device_info = coordinator.devices_info(device.id)

    @property
    def preset_modes(self) -> list[str] | None:
        _preset_modes = self._zont.get_names_heating_mode(
            self._device.modes, self._circuit
        )
        _preset_modes.append(PRESET_NONE)
        return _preset_modes

    @property
    def preset_mode(self) -> str | None:
        heating_mode_id = self._circuit.current_mode
        heating_mode = self._zont.get_heating_mode_by_id(
            self._device, heating_mode_id
        )
        if heating_mode is not None:
            return heating_mode.name
        return PRESET_NONE

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, cool mode.

        Источник правды — активный режим контура (тот же, что и
        preset_mode), иначе hvac и preset расходятся: при переключении
        current_mode и target_temp у ZONT обновляются неатомарно.
        Off-режим («Выключен») -> OFF, иной режим -> HEAT.
        Если режим не задан (ручная уставка) -> по target (<= HVAC_OFF_TEMP).
        """
        mode = self._zont.get_heating_mode_by_id(
            self._device, self._circuit.current_mode
        )
        if mode is not None:
            return HVACMode.OFF if self._mode_is_off(mode) else HVACMode.HEAT
        target = self._circuit.target_temp
        if self._circuit.is_off or (
            target is not None and target <= HVAC_OFF_TEMP
        ):
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation if supported."""
        if self._circuit.active:
            return HVACAction.HEATING
        return HVACAction.OFF

    @property
    def name(self) -> str:
        return f'{self._device.name}_{self._circuit.name}'

    @property
    def temperature_unit(self) -> str:
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float:
        return self._circuit.actual_temp

    @property
    def target_temperature(self) -> float:
        return self._circuit.target_temp

    @property
    def unique_id(self) -> str:
        return self._unique_id

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        set_temp = kwargs.get('temperature')
        if self._attr_min_temp <= set_temp <= self._attr_max_temp:
            await self._zont.set_target_temperature(
                device=self._device,
                circuit=self._circuit,
                target_temp=set_temp
            )
            await asyncio.sleep(TIME_OUT_REQUEST)
            await self.coordinator.async_request_refresh()
        else:
            raise TemperatureOutOfRangeError(
                f'Недопустимое значение температуры: {set_temp}. '
                f'Задайте температуру в пределах от {self._attr_min_temp} '
                f'до {self._attr_max_temp} включительно.'
            )

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        heating_mode = self._zont.get_heating_mode_by_name(
            self._device, preset_mode
        )
        if heating_mode is not None:
            await self._async_apply_heating_mode(heating_mode)
        else:
            await self._zont.set_target_temperature(
                device=self._device,
                circuit=self._circuit,
                target_temp=self._circuit.target_temp
            )
            self._circuit.current_mode = None
        await asyncio.sleep(TIME_OUT_REQUEST)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode.

        OFF  -> активировать режим «Выключен» (он сам ставит теплоноситель 5°).
        HEAT -> активировать режим «Комфорт» (он сам ставит 40°).
        Уставку вручную НЕ трогаем: ручная уставка сбрасывает режим в None
        (current_mode -> None) и режим не отображается активным в ЛК.
        Активация режима и ставит температуру, и делает режим активным.
        """
        if hvac_mode == HVACMode.OFF:
            mode = self._find_circuit_mode(exclude_off=False)
        elif hvac_mode == HVACMode.HEAT:
            mode = self._find_circuit_mode(exclude_off=True)
        else:
            return

        if mode is not None:
            await self._async_apply_heating_mode(mode)
        else:
            _LOGGER.warning(
                f'Режим для hvac {hvac_mode} не найден '
                f'для контура {self._circuit.name}'
            )
        await asyncio.sleep(TIME_OUT_REQUEST)
        await self.coordinator.async_request_refresh()

    @staticmethod
    def _mode_is_off(mode: HeatingModeZONT | None) -> bool:
        """True if the heating mode represents the circuit 'off' state."""
        if mode is None:
            return False
        return any(kw in mode.name.lower() for kw in _OFF_MODE_KEYWORDS)

    def _find_circuit_mode(self, exclude_off: bool) -> HeatingModeZONT | None:
        """Find first applicable circuit mode matching the off/heat filter."""
        for mode in self._device.modes:
            if self._circuit.id not in mode.can_be_applied:
                continue
            if self._mode_is_off(mode) != exclude_off:
                return mode
        return None

    async def _async_apply_heating_mode(self, heating_mode: HeatingModeZONT) -> None:
        """Apply heating mode respecting device API type (widget_type)."""
        model = self._device.device_info.model
        device_id = self._device.device_info.id
        widget_type = self._device.device_info.widget_type
        if model in MODELS_THERMOSTAT_ZONT or device_id in MODELS_THERMOSTAT_ZONT:
            await self._zont.set_heating_mode_all_circuits(
                device=self._device,
                heating_mode=heating_mode
            )
        elif widget_type == "z3k":
            await self._zont.set_heating_mode_v1(
                device=self._device,
                circuit=self._circuit,
                heating_mode_id=heating_mode.id
            )
        else:
            await self._zont.set_heating_mode(
                device=self._device,
                circuit=self._circuit,
                heating_mode_id=heating_mode.id
            )

    def __repr__(self) -> str:
        if not self.hass:
            return f'<Climate entity {self.name}>'
        return super().__repr__()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлённых данных от координатора"""
        self._device: DeviceZONT = self.coordinator.zont.get_device(
            self._device.id
        )
        self._circuit = self._zont.get_circuit(
            self._device, self._circuit.id
        )
        self.async_write_ha_state()
