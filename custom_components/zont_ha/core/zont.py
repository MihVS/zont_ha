import logging
from collections import namedtuple
from http import HTTPStatus
import json

from aiohttp import ClientResponse

from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelState
)
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .enums import TypeOfSensor, StateOfSensor
from .exceptions import StateGuardError
from .models_zont_v3 import (
    AccountZont, ErrorZont, SensorZONT, DeviceZONT, CircuitZONT,
    HeatingModeZONT, ControlsZONT, GuardZoneZONT, StatusZONT,
    ToggleButtonsZONT, ButtonZONT
)
from .models_zont_old import AccountZontOld, DeviceZontOld
from .utils import check_send_command
from ..const import (
    URL_GET_DEVICES, URL_SET_TARGET_TEMP, URL_SEND_COMMAND_ZONT_OLD,
    MIN_TEMP_AIR, MAX_TEMP_AIR, MIN_TEMP_GVS, MAX_TEMP_GVS, MIN_TEMP_FLOOR,
    MAX_TEMP_FLOOR, MATCHES_GVS, MATCHES_FLOOR,
    URL_SET_GUARD, BINARY_SENSOR_TYPES, URL_SEND_COMMAND_ZONT,
    URL_GET_DEVICES_OLD, NO_ERROR, URL_ACTIVATE_HEATING_MODE, PERCENT_BATTERY,
    ZONT_API_URL,
)

_LOGGER = logging.getLogger(__name__)

StateZont = namedtuple('StateZont', [
    'unknown', 'disabled', 'enabled', 'disabling', 'enabling'
])

state_zont = StateZont(
    'unknown', 'disabled', 'enabled', 'disabling', 'enabling'
)

TypeBinarySensorZont = namedtuple('TypeBinarySensorZont', [
    'leakage', 'smoke', 'opening', 'motion', 'discrete', 'boiler_failure',
    'room_thermostat'
])

type_binary_sensor = TypeBinarySensorZont(*BINARY_SENSOR_TYPES)


class Zont:
    """Класс контроллера zont"""

    data: AccountZont = None
    data_old: AccountZontOld
    error: ErrorZont = None

    def __init__(self,
                 hass: HomeAssistant,
                 mail: str,
                 token: str,
                 selected_devices: list[str]):
        self.headers = {
            'X-ZONT-Token': token,
            'X-ZONT-Client': mail,
            'Content-Type': 'application/json'
        }
        self.selected_devices = selected_devices
        self.mail = mail
        self.session = async_get_clientsession(hass)
        _LOGGER.debug(f'Создан объект Zont')

    async def get_update(self, old_api=False):
        """Получаем обновление данных Zont"""
        if old_api:
            url = URL_GET_DEVICES_OLD
            version = 'old'
            account = AccountZontOld
        else:
            url = URL_GET_DEVICES
            version = 'v3'
            account = AccountZont

        headers = self.headers
        response = await self.session.get(
            url=url,
            headers=headers
        )
        text = await response.text()
        status_code = response.status
        if status_code != HTTPStatus.OK:
            self.error = ErrorZont.model_validate_json(text)
            _LOGGER.error(self.error.error_ui)
            return status_code

        data_json = json.loads(text)
        devices = data_json.get('devices')
        if not self.selected_devices:
            for device in devices:
                self.selected_devices.append(str(device.get('id')))
        actual_devices = list(filter(self._is_selected, devices))
        data_json.update({'devices': actual_devices})
        self.data = account.model_validate(data_json)
        self._create_sensors()
        # if old_api:
        #     self.data_old = account.parse_raw(text)
        # else:
        #     data_json = json.loads(text)
        #     devices = data_json.get('devices')
        #     actual_devices = list(filter(self._is_selected, devices))
        #     data_json.update({'devices': actual_devices})
        #     self.data = account.model_validate(data_json)

            # self._create_sensors()
        _LOGGER.debug(f'Данные аккаунта {self.mail} обновлены. ver: {version}')
        return status_code

    def _is_selected(self, device: dict) -> bool:
        return str(device.get('id')) in self.selected_devices

    def _create_sensors(self):
        """Создает дополнительные сенсоры"""
        for device in self.data.devices:
            self._create_radio_sensors(device)

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

    # @staticmethod
    # def _convert_value_battery(value: float) -> int:
    #     """Преобразовывает напряжение батарейки в уровень заряда в %"""
    #     value = round(value, 1)
    #     if value > 3.0:
    #         return 100
    #     elif value < 2.2:
    #         return 0
    #     else:
    #         return PERCENT_BATTERY[value]
    #
    # @staticmethod
    # def _create_error_boiler_sensors(device: DeviceZONT):
    #     """Создаёт дополнительные сенсоры ошибок котла"""
    #     for boiler in device.boiler_circuits:
    #         code_err = boiler.error_oem
    #         text = boiler.error_text
    #         if code_err != NO_ERROR:
    #             code_err = code_err[11:]
    #             text = f': {boiler.error_text}'
    #         if code_err == NO_ERROR and boiler.status == 'failure':
    #             code_err = 'Ошибка'
    #         device.sensors.append(SensorZONT(
    #             id=f'{boiler.id}_boiler',
    #             name=f'{boiler.name}_ошибка',
    #             type='boiler_failure',
    #             status='ok',
    #             value=code_err + text,
    #             unit='txt'
    #         ))

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

    # @staticmethod
    # def get_heating_circuit(
    #         device: DeviceZONT, circuit_id: int
    # ) -> CircuitZONT | None:
    #     """Получить сенсор по его id и id устройства"""
    #     return next(
    #         (circuit for circuit in device.circuits
    #          if circuit.id == circuit_id), None
    #     )

    # @staticmethod
    # def get_guard_zone(
    #         device: DeviceZONT, guard_zone_id: int
    # ) -> GuardZoneZONT | None:
    #     """Получить охранную зону по её id и id устройства"""
    #     return next(
    #         (guard_zone for guard_zone in device.guard_zones
    #          if guard_zone.id == guard_zone_id), None
    #     )
    #
    # @staticmethod
    # def need_repeat_update(state_guard_zone: str) -> bool:
    #     values = (state_zont.enabling, state_zont.disabling)
    #     if state_guard_zone in values:
    #         return True
    #     return False
    #
    # @staticmethod
    # def get_state_guard_zone_for_ha(
    #         guard_zone: GuardZoneZONT
    # ) -> AlarmControlPanelState:
    #     """Получить статус охранной зоны"""
    #     if guard_zone.alarm:
    #         return AlarmControlPanelState.TRIGGERED
    #     match guard_zone.state:
    #         case state_zont.unknown:
    #             return STATE_UNAVAILABLE
    #         case state_zont.disabled:
    #             return AlarmControlPanelState.DISARMED
    #         case state_zont.enabled:
    #             return AlarmControlPanelState.ARMED_AWAY
    #         case state_zont.disabling:
    #             return AlarmControlPanelState.DISARMING
    #         case state_zont.enabling:
    #             return AlarmControlPanelState.ARMING
    #         case _:
    #             raise StateGuardError(
    #                 f'Неизвестный статус охранной зоны: {guard_zone.state}'
    #             )
    #
    # @staticmethod
    # def get_heating_mode_by_id(
    #         device: DeviceZONT, heating_mode_id: int
    # ) -> HeatingModeZONT | None:
    #     """Получить name отопительного режима по его id"""
    #     return next(
    #         (heating_mode for heating_mode in device.heating_modes
    #          if heating_mode.id == heating_mode_id), None
    #     )
    #
    # @staticmethod
    # def get_heating_mode_by_name(
    #         device: DeviceZONT, heating_mode_name: str
    # ) -> HeatingModeZONT | None:
    #     """Получить id отопительного режима по его name"""
    #     return next(
    #         (heating_mode for heating_mode in device.heating_modes
    #          if heating_mode.name == heating_mode_name), None
    #     )
    #
    # @staticmethod
    # def get_names_heating_mode(
    #         heating_modes: list[HeatingModeZONT]
    # ) -> list[str]:
    #     """Возвращает список названий отопительных режимов"""
    #     return [heating_mode.name for heating_mode in heating_modes]

    # @staticmethod
    # def _validate_min_max_values_temp(min_temp, max_temp) -> bool:
    #     if not (isinstance(min_temp, int) and isinstance(max_temp, int)):
    #         return False
    #     if min_temp < 0 and max_temp > 80:
    #         return False
    #     return True
    #
    # def get_min_max_values_temp(
    #        self, heating_circuit: CircuitZONT) -> tuple[int, int]:
    #     """
    #     Функция для получения максимальной и минимальной температур
    #     по контуру отопления.
    #     """
    #     val_min = heating_circuit.target_min
    #     val_max = heating_circuit.target_max
    #     if self._validate_min_max_values_temp(val_min, val_max):
    #         return val_min, val_max
    #     _LOGGER.warning(f'Не удалось получить пределы регулировки температуры'
    #                     f' для контура: {heating_circuit.id}. Значения взяты'
    #                     f' исходя из названия контура.')
    #     circuit_name = heating_circuit.name
    #     val_min, val_max = MIN_TEMP_AIR, MAX_TEMP_AIR
    #     circuit_name = circuit_name.lower().strip()
    #     matches_gvs = MATCHES_GVS
    #     matches_floor = MATCHES_FLOOR
    #     if any([x in circuit_name for x in matches_gvs]):
    #         val_min, val_max = MIN_TEMP_GVS, MAX_TEMP_GVS
    #     elif any([x in circuit_name for x in matches_floor]):
    #         val_min, val_max = MIN_TEMP_FLOOR, MAX_TEMP_FLOOR
    #
    #     return val_min, val_max

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

    # @check_send_command
    # async def set_target_temperature(
    #         self, device: DeviceZONT, heating_circuit: CircuitZONT,
    #         target_temp: float
    # ) -> ClientResponse:
    #     """Отправка команды на установку нужной температуры в контуре."""
    #     _LOGGER.info(f'Отправлена уставка температуры на {target_temp}')
    #     return await self.session.post(
    #         url=URL_SET_TARGET_TEMP,
    #         json={
    #             'device_id': device.id,
    #             'circuit_id': heating_circuit.id,
    #             'target_temp': target_temp
    #         },
    #         headers=self.headers
    #     )
    #
    # async def set_heating_mode_all_circuit(
    #         self, device: DeviceZONT, heating_mode_id: int
    # ) -> ClientResponse:
    #     """Отправка команды на установку нужного режима для всех контуров."""
    #     response = await self.session.post(
    #         url=URL_ACTIVATE_HEATING_MODE,
    #         json={
    #             'device_id': device.id,
    #             'mode_id': heating_mode_id
    #         },
    #         headers=self.headers
    #     )
    #     _LOGGER.debug(await response.text())
    #     return response
    #
    # async def set_heating_mode(
    #         self, device: DeviceZONT, heating_circuit: CircuitZONT,
    #         heating_mode_id: int
    # ) -> ClientResponse:
    #     """Отправка команды на установку нужного режима для контура."""
    #     response = await self.session.post(
    #         url=URL_SEND_COMMAND_ZONT_OLD,
    #         json={
    #             'device_id': device.id,
    #             'command_name': 'SelectHeatingModeForCircuit',
    #             'object_id': heating_circuit.id,
    #             'command_args': {'mode_id': heating_mode_id},
    #             'request_time': 1000,
    #             'is_guaranteed': True
    #         },
    #         headers=self.headers
    #     )
    #     _LOGGER.debug(await response.text())
    #     return response
    #
    # @check_send_command
    # async def set_heating_mode_all_heating_circuits(
    #         self, device: DeviceZONT, heating_mode: HeatingModeZONT
    # ) -> ClientResponse:
    #     """Отправка команды на установку нужного режима для всех контуров."""
    #     return await self.session.post(
    #         url=URL_SEND_COMMAND_ZONT,
    #         json={
    #             'device_id': device.id,
    #             'mode_id': heating_mode.id
    #         },
    #         headers=self.headers
    #     )

    @check_send_command
    async def switch_button(
            self, device: DeviceZONT,
            button: ToggleButtonsZONT | ButtonZONT,
            command: bool,
    ) -> ClientResponse:
        """Отправка команды на установку нужной температуры в контуре."""
        return await self.session.post(
            url=f'{ZONT_API_URL}devices/{device.id}/controls/{button.id}/actions/trigger',
            json={
                'target_state': command
            },
            headers=self.headers
        )

    # @check_send_command
    # async def toggle_alarm(
    #         self, device: DeviceZONT, guard_zone: GuardZoneZONT,
    #         command: bool
    # ) -> ClientResponse:
    #     """Отправка команды на изменение состояния охранной зоны."""
    #     return await self.session.post(
    #         url=URL_SET_GUARD,
    #         json={
    #             'device_id': device.id,
    #             'zone_id': guard_zone.id,
    #             'enable': command
    #         },
    #         headers=self.headers
    #     )
