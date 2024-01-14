import logging

from aiohttp import ClientResponse

from homeassistant.helpers.aiohttp_client import async_get_clientsession, \
    HassClientResponse
from homeassistant.helpers.typing import HomeAssistantType
from .models_zont import (
    AccountZont, ErrorZont, SensorZONT, DeviceZONT, HeatingCircuitZONT,
    HeatingModeZONT
)
from .utils import check_send_command
from ..const import URL_GET_DEVICES, URL_SET_TARGET_TEMP, \
    URL_SEND_COMMAND_ZONT_OLD

_LOGGER = logging.getLogger(__name__)


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
        _LOGGER.debug(f'Создан объект Zont')

    async def get_update(self):
        """Получаем обновление данных объекта Zont"""
        headers = self.headers
        _LOGGER.debug(headers)
        response = await self.session.post(
            url=URL_GET_DEVICES,
            headers=headers
        )
        text = await response.text()
        status_code = response.status
        if status_code != 200:
            self.error = ErrorZont.parse_raw(text)
            _LOGGER.error(self.error.error_ui)
            return status_code
        self.data = AccountZont.parse_raw(text)
        _LOGGER.debug(f'Данные аккаунта {self.mail} обновлены')
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

    def get_heating_circuit(
            self, device_id: int, heating_circuit_id: int
    ) -> HeatingCircuitZONT | None:
        """Получить сенсор по его id и id устройства"""
        device = self.get_device(device_id)
        return next(
            (heating_circuit for heating_circuit in device.heating_circuits
             if heating_circuit.id == heating_circuit_id), None
        )

    def get_heating_mode_by_id(
            self, device_id: int, heating_mode_id: int
    ) -> HeatingModeZONT | None:
        """Получить name отопительного режима по его id"""
        device = self.get_device(device_id)
        return next(
            (heating_mode for heating_mode in device.heating_modes
             if heating_mode.id == heating_mode_id), None
        )

    def get_heating_mode_by_name(
            self, device_id: int, heating_mode_name: str
    ) -> HeatingModeZONT | None:
        """Получить id отопительного режима по его name"""
        device = self.get_device(device_id)
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
        val_min, val_max = 5, 35
        circuit_name = circuit_name.lower().strip()
        matches_gvs = ('гвс', 'горяч', 'вода',)
        matches_floor = ('пол', 'тёплый',)
        if any([x in circuit_name for x in matches_gvs]):
            val_min, val_max = 5, 75
        elif any([x in circuit_name for x in matches_floor]):
            val_min, val_max = 15, 50

        return val_min, val_max

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
        _LOGGER.warning(await response.text())
        return response

    # {
    #     "device_id": 278936,
    #     "command_name": "SelectHeatingModeForCircuit",
    #     "object_id": 8550,
    #     "command_args": {"mode_id": 8389},
    #     "request_time": 1000,
    #     "is_guaranteed": true
    # }
