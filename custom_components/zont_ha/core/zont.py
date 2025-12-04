import json
import logging
from collections import namedtuple
from http import HTTPStatus

from aiohttp import ClientResponse

from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelState
)
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .enums import GuardState
from .enums import TypeOfSensor, StateOfSensor, TypeOfCircuit
from .exceptions import StateGuardError
from .models_zont_v1 import AccountZontOld, DeviceZontOld
from .models_zont_v3 import (
    AccountZont, ErrorZont, SensorZONT, DeviceZONT, CircuitZONT,
    HeatingModeZONT, GuardZoneZONT, StatusZONT,
    ToggleButtonsZONT, ButtonZONT
)
from .utils import check_send_command
from ..const import (
    URL_GET_DEVICES, URL_SEND_COMMAND_ZONT_OLD,
    MIN_TEMP_AIR, MAX_TEMP_AIR, MIN_TEMP_GVS, MAX_TEMP_GVS, MIN_TEMP_FLOOR,
    MAX_TEMP_FLOOR, MATCHES_GVS, MATCHES_FLOOR,
    BINARY_SENSOR_TYPES, URL_GET_DEVICES_OLD, NO_ERROR,
    ZONT_API_URL,
)

_LOGGER = logging.getLogger(__name__)

StateZont = namedtuple('StateZont', [
    'unknown', 'disabled', 'enabled', 'disabling', 'enabling'
])

TypeBinarySensorZont = namedtuple('TypeBinarySensorZont', [
    'leakage', 'smoke', 'opening', 'motion', 'discrete', 'boiler_failure',
    'room_thermostat'
])

type_binary_sensor = TypeBinarySensorZont(*BINARY_SENSOR_TYPES)


class Zont:
    """Класс контроллера zont"""

    data: AccountZont = None
    data_old: AccountZontOld = AccountZontOld()
    error: ErrorZont = None

    def __init__(self,
                 hass: HomeAssistant,
                 mail: str,
                 token: str,
                 selected_devices: list[str] | None = None):
        self.headers = {
            'X-ZONT-Token': token,
            'X-ZONT-Client': mail,
            'Content-Type': 'application/json'
        }
        if selected_devices is None:
            selected_devices = []
        self.selected_devices = selected_devices
        self.mail = mail
        self.session = async_get_clientsession(hass)
        _LOGGER.debug(f'Создан объект Zont')

    async def init_old_data(self):
        """Инициализирует данные из API V1"""
        headers = self.headers
        response = await self.session.post(
            url=URL_GET_DEVICES_OLD,
            headers=headers
        )
        text = await response.text()
        status_code = response.status
        if status_code != HTTPStatus.OK:
            _LOGGER.error(f'Не удалось получить данные из API V1. '
                          f'Status code: {status_code}. Text: {text}')
            return
        self.data_old = AccountZontOld.model_validate_json(text)
        _LOGGER.debug(f'For {self.mail} initialized old_data from API V1.')

    async def get_update(self):
        """Получаем обновление данных Zont"""
        headers = self.headers
        response = await self.session.get(
            url=URL_GET_DEVICES,
            headers=headers
        )
        text = await response.text()
        status_code = response.status
        if status_code != HTTPStatus.OK:
            self.error = ErrorZont.model_validate_json(text)
            _LOGGER.error(self.error.error_ui)
            return

        data_json = json.loads(text)
        devices = data_json.get('devices')
        if not self.selected_devices:
            for device in devices:
                self.selected_devices.append(str(device.get('id')))
        actual_devices = list(filter(self._is_selected, devices))
        data_json.update({'devices': actual_devices})
        self.data = AccountZont.model_validate(data_json)
        self._create_sensors()
        _LOGGER.debug(f'Данные аккаунта {self.mail} обновлены. API V3')
        return status_code

    def _is_selected(self, device: dict) -> bool:
        return str(device.get('id')) in self.selected_devices

    def _create_sensors(self):
        """Создает дополнительные сенсоры"""
        for device in self.data.devices:
            self._create_radio_sensors(device)
            self._create_sensors_of_boiler(device)

    @staticmethod
    def _create_radio_sensors(device: DeviceZONT):
        """
        Создает дополнительные сенсоры
        уровня батареи и связи для радио датчиков
        """
        for i in range(len(device.sensors)):
            sensor = device.sensors[i]
            if sensor.battery:
                device.sensors.append(SensorZONT(
                    id=f'{sensor.id}_rssi',
                    name=f'{sensor.name}_rssi',
                    type=TypeOfSensor.SIGNAL_STRENGTH,
                    status=StateOfSensor.OK,
                    value=sensor.rssi,
                    unit='дБм'
                ))
                device.sensors.append(SensorZONT(
                    id=f'{sensor.id}_battery',
                    name=f'{sensor.name}_battery',
                    type=TypeOfSensor.BATTERY,
                    status=StateOfSensor.OK,
                    value=sensor.battery,
                    unit='%'
                ))

    @staticmethod
    def _create_boiler_error_sensor(boiler: CircuitZONT, device: DeviceZONT):
        """Создает сенсор ошибок котла."""
        text = NO_ERROR
        if boiler.error is not None:
            text = f'{boiler.error.oem} | {boiler.error.text}'
        device.sensors.append(SensorZONT(
            id=f'{boiler.id}_boiler_error',
            name=f'{boiler.name}_ошибка',
            type=TypeOfSensor.BOILER_FAILURE_TEXT,
            status=StateOfSensor.OK,
            value=text,
            unit='txt'
        ))

    @staticmethod
    def _create_boiler_active_sensor(boiler: CircuitZONT, device: DeviceZONT):
        """Создает сенсор работы котла."""
        device.sensors.append(SensorZONT(
            id=f'{boiler.id}_boiler',
            name=f'{boiler.name}_состояние',
            type=TypeOfSensor.ROOM_THERMOSTAT,
            status=StateOfSensor.OK,
            triggered=boiler.active,
        ))

    def _create_sensors_of_boiler(self, device: DeviceZONT):
        """Создаёт дополнительные сенсоры котла"""
        for circuit in device.circuits:
            if circuit.type == TypeOfCircuit.BOILER:
                self._create_boiler_error_sensor(circuit, device)
                self._create_boiler_active_sensor(circuit, device)

    def get_device(self, device_id: int) -> DeviceZONT | None:
        """Получить устройство по его id"""
        return next(
            (device for device in self.data.devices if device.id == device_id),
            None
        )

    def get_device_old(self, device_id: int) -> DeviceZontOld | None:
        """Получить устройство по его id для старого API"""
        return next(
            (device for device in self.data_old.devices
             if device.id == device_id),
            None
        )

    def get_sensor(
            self, device_id: int, sensor_id: int | str
    ) -> SensorZONT | None:
        """Получить сенсор по его id и id устройства"""
        device = self.get_device(device_id)
        return next(
            (sensor for sensor in device.sensors if sensor.id == sensor_id),
            None
        )

    @staticmethod
    def get_circuit(
            device: DeviceZONT, circuit_id: int
    ) -> CircuitZONT | None:
        """Получить контур отопления по его id и id устройства"""
        return next(
            (circuit for circuit in device.circuits
             if circuit.id == circuit_id), None
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
    def need_repeat_update(state_guard_zone: GuardState) -> bool:
        values = (GuardState.ENABLING, GuardState.DISABLING)
        if state_guard_zone in values:
            return True
        return False

    @staticmethod
    def get_state_guard_zone_for_ha(
            guard_zone: GuardZoneZONT
    ) -> AlarmControlPanelState:
        """Получить статус охранной зоны"""
        if guard_zone.alarm:
            return AlarmControlPanelState.TRIGGERED
        match guard_zone.state:
            case GuardState.UNKNOWN:
                return STATE_UNAVAILABLE
            case GuardState.DISABLED:
                return AlarmControlPanelState.DISARMED
            case GuardState.ENABLED:
                return AlarmControlPanelState.ARMED_AWAY
            case GuardState.DISABLING:
                return AlarmControlPanelState.DISARMING
            case GuardState.ENABLING:
                return AlarmControlPanelState.ARMING
            case _:
                raise StateGuardError(
                    f'Неизвестный статус охранной зоны: {guard_zone.state}'
                )

    @staticmethod
    def get_heating_mode_by_id(
            device: DeviceZONT, heating_mode_id: int
    ) -> HeatingModeZONT | None:
        """Получить name отопительного режима по его id"""
        return next(
            (heating_mode for heating_mode in device.modes
             if heating_mode.id == heating_mode_id), None
        )

    @staticmethod
    def get_heating_mode_by_name(
            device: DeviceZONT, heating_mode_name: str
    ) -> HeatingModeZONT | None:
        """Получить id отопительного режима по его name"""
        return next(
            (heating_mode for heating_mode in device.modes
             if heating_mode.name == heating_mode_name), None
        )

    @staticmethod
    def get_names_heating_mode(
            heating_modes: list[HeatingModeZONT], circuit: CircuitZONT
    ) -> list[str]:
        """Возвращает список названий отопительных режимов для контура."""
        names_heating_mode = []
        for heating_mode in heating_modes:
            if circuit.id in heating_mode.can_be_applied:
                names_heating_mode.append(heating_mode.name)
        return names_heating_mode

    @staticmethod
    def _validate_min_max_values_temp(min_temp, max_temp) -> bool:
        if not (isinstance(min_temp, float) and isinstance(max_temp, float)):
            return False
        if min_temp < 0 and max_temp > 90:
            return False
        return True

    def get_min_max_values_temp(
           self, circuit: CircuitZONT) -> tuple[float, float]:
        """
        Функция для получения максимальной и минимальной температур
        по контуру отопления.
        """
        val_min = circuit.min
        val_max = circuit.max
        if self._validate_min_max_values_temp(val_min, val_max):
            return val_min, val_max
        _LOGGER.warning(f'Не удалось получить пределы регулировки температуры'
                        f' для контура: "{circuit.name}". Значения взяты'
                        f' исходя из названия контура.')
        circuit_name = circuit.name
        val_min, val_max = MIN_TEMP_AIR, MAX_TEMP_AIR
        circuit_name = circuit_name.lower().strip()
        if any([x in circuit_name for x in MATCHES_GVS]):
            val_min, val_max = MIN_TEMP_GVS, MAX_TEMP_GVS
        elif any([x in circuit_name for x in MATCHES_FLOOR]):
            val_min, val_max = MIN_TEMP_FLOOR, MAX_TEMP_FLOOR
        return val_min, val_max

    def get_status_control(
            self, device_id: int, status_id: int) -> StatusZONT:
        device = self.get_device(device_id)
        return next((status for status in device.controls.statuses if
                     (status.id == status_id)), None)

    def get_toggle_button(
            self, device_id: int, toggle_button_id: int) -> ToggleButtonsZONT:
        device = self.get_device(device_id)
        return next(
            (toggle_button for toggle_button in device.controls.toggle_buttons
             if (toggle_button.id == toggle_button_id)), None)

    @check_send_command
    async def set_target_temperature(
            self, device: DeviceZONT, circuit: CircuitZONT,
            target_temp: float
    ) -> ClientResponse:
        """Отправка команды на установку нужной температуры в контуре."""
        _LOGGER.info(f'Отправлена уставка температуры на {target_temp}')
        return await self.session.post(
            url=f'{ZONT_API_URL}devices/{device.id}/circuits/'
                f'{circuit.id}/actions/target-temp',
            json={'target_temp': target_temp},
            headers=self.headers
        )

    @check_send_command
    async def set_heating_mode(
            self, device: DeviceZONT, circuit: CircuitZONT,
            heating_mode_id: int
    ) -> ClientResponse:
        """Отправка команды на установку нужного режима для контура."""
        return await self.session.post(
            url=f'{ZONT_API_URL}devices/{device.id}/modes/'
                f'{heating_mode_id}/actions/activate',
            json={'circuit_id': circuit.id},
            headers=self.headers
        )

    async def set_heating_mode_v1(
            self, device: DeviceZONT, circuit: CircuitZONT,
            heating_mode_id: int
    ) -> ClientResponse:
        """Отправка команды на установку нужного режима для контура."""
        response = await self.session.post(
            url=URL_SEND_COMMAND_ZONT_OLD,
            json={
                'device_id': device.id,
                'command_name': 'SelectHeatingModeForCircuit',
                'object_id': circuit.id,
                'command_args': {'mode_id': heating_mode_id},
                'request_time': 1000,
                'is_guaranteed': True
            },
            headers=self.headers
        )
        _LOGGER.debug(await response.text())
        return response

    @check_send_command
    async def set_heating_mode_all_circuits(
            self, device: DeviceZONT, heating_mode: HeatingModeZONT
    ) -> ClientResponse:
        """Отправка команды на установку нужного режима для всех контуров."""
        return await self.session.post(
            url=f'{ZONT_API_URL}devices/{device.id}/modes/'
                f'{heating_mode.id}/actions/activate',
            headers=self.headers
        )

    @check_send_command
    async def switch_button(
            self, device: DeviceZONT,
            button: ToggleButtonsZONT | ButtonZONT,
            command: bool,
    ) -> ClientResponse:
        """Отправка команды на установку нужной температуры в контуре."""
        return await self.session.post(
            url=f'{ZONT_API_URL}devices/{device.id}/controls/'
                f'{button.id}/actions/trigger',
            json={'target_state': command},
            headers=self.headers
        )

    @check_send_command
    async def toggle_alarm(
            self, device: DeviceZONT, guard_zone: GuardZoneZONT,
            command: bool
    ) -> ClientResponse:
        """Отправка команды на изменение состояния охранной зоны."""
        return await self.session.post(
            url=f'{ZONT_API_URL}devices/{device.id}/guard-zones/'
                f'{guard_zone.id}/actions/activate',
            json={
                'zone_id': guard_zone.id,
                'enable': command
            },
            headers=self.headers
        )
