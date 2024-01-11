import logging

from aiohttp import ClientSession

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import HomeAssistantType

from ..const import URL_GET_DEVICES
from .models_zont import (
    AccountZont, ErrorZont, SensorZONT, DeviceZONT, HeatingCircuitZONT,
    HeatingModeZONT
)

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

    def get_sensor(self, device_id: int, sensor_id: int) -> SensorZONT | None:
        """Получить сенсор по его id и id устройства"""

        device = self.get_device(device_id)
        return next(
            (sensor for sensor in device.sensors if sensor.id == sensor_id),
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

    @staticmethod
    def _is_valid_name_heating_mode(name: str) -> bool:
        """Проверяет валидно ли название для отопительного режима."""

        invalid_names = ('газ', 'электр', 'котл', 'котёл', 'котел')
        name = name.lower().strip()
        for invalid_name in invalid_names:
            if invalid_name in name:
                return False
        return True

    def get_heating_modes(self, device: DeviceZONT) -> list[HeatingModeZONT]:
        """
        Получить валидные отопительные режимы.
        От API приходит ответ вместе с котловыми режимами.
        Метод фильтрует режимы по названию.
        """

        return [
            heating_mode for heating_mode in device.heating_modes
            if self._is_valid_name_heating_mode(heating_mode.name)
        ]

    def get_heating_mode(
            self, device_id: int, heating_mode_id: int
    ) -> HeatingModeZONT:
        """Получить отопительный режим по его id"""

        device = self.get_device(device_id)
        return next(
            (heating_mode for heating_mode in device.heating_modes
             if heating_mode.id == heating_mode_id), None
        )

    @staticmethod
    def get_names_get_heating_mode(
            heating_modes: list[HeatingModeZONT]
    ) -> list[str]:
        """Возвращает список названий отопительных режимов"""

        return [heating_mode.name for heating_mode in heating_modes]
