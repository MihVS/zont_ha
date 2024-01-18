import logging
from collections import namedtuple
from http import HTTPStatus

from aiohttp import ClientResponse

from homeassistant.const import (
    STATE_ALARM_TRIGGERED, STATE_UNAVAILABLE, STATE_ALARM_DISARMED,
    STATE_ALARM_ARMED_HOME, STATE_ALARM_DISARMING, STATE_ALARM_ARMING
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import HomeAssistantType
from .exceptions import StateGuardError
from .models_zont import (
    AccountZont, ErrorZont, SensorZONT, DeviceZONT, HeatingCircuitZONT,
    HeatingModeZONT, CustomControlZONT, GuardZoneZONT
)
from .utils import check_send_command
from ..const import (
    URL_GET_DEVICES, URL_SET_TARGET_TEMP, URL_SEND_COMMAND_ZONT_OLD,
    MIN_TEMP_AIR, MAX_TEMP_AIR, MIN_TEMP_GVS, MAX_TEMP_GVS, MIN_TEMP_FLOOR,
    MAX_TEMP_FLOOR, MATCHES_GVS, MATCHES_FLOOR, URL_TRIGGER_CUSTOM_BUTTON,
    URL_SET_GUARD, BINARY_SENSOR_TYPES,
)

_LOGGER = logging.getLogger(__name__)

StateZont = namedtuple('StateZont', [
    'unknown', 'disabled', 'enabled', 'disabling', 'enabling'
])

state_zont = StateZont(
    'unknown', 'disabled', 'enabled', 'disabling', 'enabling'
)

TypeBinarySensorZont = namedtuple('TypeBinarySensorZont', [
    'leakage', 'smoke', 'opening', 'motion'
])

type_binary_sensor = TypeBinarySensorZont(*BINARY_SENSOR_TYPES)


class Zont:
    """Класс контроллера zont"""

    data: AccountZont = None
    error: ErrorZont = None

    def __init__(self, hass: HomeAssistantType, mail: str, token: str):
        self.headers = {
            'X-ZONT-Token': token,
            'X-ZONT-Client': mail,
            'Content-Type': 'application/json'
        }
        self.mail = mail
        self.session = async_get_clientsession(hass)
        _LOGGER.warning(f'Создан объект Zont')

    async def get_update(self):
        """Получаем обновление данных объекта Zont"""
        headers = self.headers
        response = await self.session.post(
            url=URL_GET_DEVICES,
            headers=headers
        )
        text = await response.text()
        status_code = response.status
        if status_code != HTTPStatus.OK:
            self.error = ErrorZont.parse_raw(text)
            _LOGGER.error(self.error.error_ui)
            return status_code
        self.data = AccountZont.parse_raw(text)
        _LOGGER.info(f'Данные аккаунта {self.mail} обновлены')
        return status_code

    def get_device(self, device_id: int) -> DeviceZONT | None:
        """Получить устройство по его id"""
        return next(
            (device for device in self.data.devices if device.id == device_id),
            None
        )

    def get_sensor(
            self, device_id: int, sensor_id: int | str
    ) -> SensorZONT | None:
        """Получить сенсор по его id и id устройства"""
        device = self.get_device(device_id)
        all_sensors = device.sensors + device.ot_sensors
        return next(
            (sensor for sensor in all_sensors if sensor.id == sensor_id),
            None
        )

    @staticmethod
    def get_heating_circuit(
            device: DeviceZONT, heating_circuit_id: int
    ) -> HeatingCircuitZONT | None:
        """Получить сенсор по его id и id устройства"""
        return next(
            (heating_circuit for heating_circuit in device.heating_circuits
             if heating_circuit.id == heating_circuit_id), None
        )

    @staticmethod
    def get_guard_zone(
            device: DeviceZONT, guard_zone_id: int
    ) -> GuardZoneZONT | None:
        """Получить охранную зону по её id и id устройства"""
        return next(
            (guard_zone for guard_zone in device.guard_zones
             if guard_zone.id == guard_zone_id), None
        )

    @staticmethod
    def need_repeat_update(state_guard_zone: str) -> bool:
        values = (state_zont.enabling, state_zont.disabling)
        if state_guard_zone in values:
            return True
        return False

    @staticmethod
    def get_state_guard_zone_for_ha(guard_zone: GuardZoneZONT) -> str:
        """Получить статус охранной зоны"""
        if guard_zone.alarm:
            return STATE_ALARM_TRIGGERED
        match guard_zone.state:
            case state_zont.unknown:
                return STATE_UNAVAILABLE
            case state_zont.disabled:
                return STATE_ALARM_DISARMED
            case state_zont.enabled:
                return STATE_ALARM_ARMED_HOME
            case state_zont.disabling:
                return STATE_ALARM_DISARMING
            case state_zont.enabling:
                return STATE_ALARM_ARMING
            case _:
                raise StateGuardError(
                    f'Неизвестный статус охранной зоны: {guard_zone.state}'
                )

    @staticmethod
    def get_voltage(device: DeviceZONT, sensor_id: int = 0) -> int | None:
        return next(
            (sensor.value for sensor in device.sensors
             if sensor.id == sensor_id), None
        )

    @staticmethod
    def _is_on_leakage(voltage: float, current_value: float) -> bool:
        return not 0.25 * voltage < current_value < 0.75 * voltage

    @staticmethod
    def _is_on_smoke(voltage: float, current_value: float) -> bool:
        return not 0.52 * voltage < current_value < 0.85 * voltage

    @staticmethod
    def _is_on_contact(voltage: float, current_value: float) -> bool:
        return current_value > 0.6 * voltage

    def is_on_binary(self, device: DeviceZONT, sensor: SensorZONT) -> bool:
        current_value = sensor.value
        if current_value is None:
            return False
        voltage = self.get_voltage(device)
        if voltage is None:
            return False
        match sensor.type:
            case type_binary_sensor.leakage:
                return self._is_on_leakage(voltage, current_value)
            case type_binary_sensor.smoke:
                return self._is_on_smoke(voltage, current_value)
            case type_binary_sensor.opening | type_binary_sensor.motion:
                return self._is_on_contact(voltage, current_value)
            case _:
                _LOGGER.warning(f"Unknown sensor type: {sensor.type}")
                return False

    @staticmethod
    def get_heating_mode_by_id(
            device: DeviceZONT, heating_mode_id: int
    ) -> HeatingModeZONT | None:
        """Получить name отопительного режима по его id"""
        return next(
            (heating_mode for heating_mode in device.heating_modes
             if heating_mode.id == heating_mode_id), None
        )

    @staticmethod
    def get_heating_mode_by_name(
            device: DeviceZONT, heating_mode_name: str
    ) -> HeatingModeZONT | None:
        """Получить id отопительного режима по его name"""
        return next(
            (heating_mode for heating_mode in device.heating_modes
             if heating_mode.name == heating_mode_name), None
        )

    @staticmethod
    def get_names_heating_mode(
            heating_modes: list[HeatingModeZONT]
    ) -> list[str]:
        """Возвращает список названий отопительных режимов"""
        return [heating_mode.name for heating_mode in heating_modes]

    @staticmethod
    def get_min_max_values_temp(circuit_name: str) -> tuple[int, int]:
        """
        Функция для получения максимальной и минимальной температур
        по имени контура отопления.
        """
        val_min, val_max = MIN_TEMP_AIR, MAX_TEMP_AIR
        circuit_name = circuit_name.lower().strip()
        matches_gvs = MATCHES_GVS
        matches_floor = MATCHES_FLOOR
        if any([x in circuit_name for x in matches_gvs]):
            val_min, val_max = MIN_TEMP_GVS, MAX_TEMP_GVS
        elif any([x in circuit_name for x in matches_floor]):
            val_min, val_max = MIN_TEMP_FLOOR, MAX_TEMP_FLOOR

        return val_min, val_max

    def get_custom_control(self, device_id: int, control_id: int
                           ) -> CustomControlZONT:
        device = self.get_device(device_id)
        return next(
            (control for control in device.custom_controls
             if control.id == control_id), None
        )

    @check_send_command
    async def set_target_temperature(
            self, device: DeviceZONT, heating_circuit: HeatingCircuitZONT,
            target_temp: float
    ) -> ClientResponse:
        """Отправка команды на установку нужной температуры в контуре."""
        return await self.session.post(
            url=URL_SET_TARGET_TEMP,
            json={
                'device_id': device.id,
                'circuit_id': heating_circuit.id,
                'target_temp': target_temp
            },
            headers=self.headers
        )

    async def set_heating_mode(
            self, device: DeviceZONT, heating_circuit: HeatingCircuitZONT,
            heating_mode_id: int
    ) -> ClientResponse:
        """Отправка команды на установку нужного режима для контура."""
        response = await self.session.post(
            url=URL_SEND_COMMAND_ZONT_OLD,
            json={
                'device_id': device.id,
                'command_name': 'SelectHeatingModeForCircuit',
                'object_id': heating_circuit.id,
                'command_args': {'mode_id': heating_mode_id},
                'request_time': 1000,
                'is_guaranteed': True
            },
            headers=self.headers
        )
        _LOGGER.debug(await response.text())
        return response

    @check_send_command
    async def toggle_switch(
            self, device: DeviceZONT, control: CustomControlZONT,
            command: bool
    ) -> ClientResponse:
        """Отправка команды на установку нужной температуры в контуре."""
        return await self.session.post(
            url=URL_TRIGGER_CUSTOM_BUTTON,
            json={
                'device_id': device.id,
                'control_id': control.id,
                'target_state': command
            },
            headers=self.headers
        )

    @check_send_command
    async def toggle_alarm(
            self, device: DeviceZONT, guard_zone: GuardZoneZONT,
            command: bool
    ) -> ClientResponse:
        """Отправка команды на изменение состояния охранной зоны."""
        return await self.session.post(
            url=URL_SET_GUARD,
            json={
                'device_id': device.id,
                'zone_id': guard_zone.id,
                'enable': command
            },
            headers=self.headers
        )
