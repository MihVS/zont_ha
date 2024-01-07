import logging

from aiohttp import ClientSession

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import HomeAssistantType

from ..const import URL_GET_DEVICES
from .models_zont import AccountZont, ErrorZont, SensorZONT

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

    def get_sensor(self, device_id: int, sensor_id: int) -> SensorZONT | None:
        """Получить сенсор по его id и id устройства"""

        for device in self.data.devices:
            if device.id == device_id:
                for sensor in device.sensors:
                    if sensor.id == sensor_id:
                        return sensor
