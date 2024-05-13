import logging
from http import HTTPStatus

from aiohttp import ClientResponse

from .exceptions import ResponseZontError
from ..const import HEATING_MODES, VALID_UNITS, VALID_TYPE_SENSOR
from .models_zont import SensorZONT

_LOGGER = logging.getLogger(__name__)


def check_send_command(func):
    """
    Декоратор для проверки успешной отправки команды
    управления параметрами контроллера zont.
    """
    async def check_response(*args, **kwargs):
        device = kwargs.get('device')
        heating_circuit = kwargs.get('heating_circuit')
        heating_mode = kwargs.get('heating_mode')
        target_temp = kwargs.get('target_temp')
        guard_zone = kwargs.get('guard_zone')
        custom_control = kwargs.get('control')
        command = kwargs.get('command')

        if target_temp is not None:
            control = heating_circuit
            set_value = target_temp
        elif custom_control is not None:
            control = custom_control
            set_value = command
        elif guard_zone is not None:
            control = guard_zone
            set_value = command
        elif heating_mode is not None:
            control = heating_mode
            set_value = 'Установлен во всех контурах'
        else:
            return func

        response: ClientResponse = await func(*args, **kwargs)
        status = response.status
        data = await response.json()
        if status == HTTPStatus.OK:
            _LOGGER.debug(f'Успешный запрос к API zont: {status}')
            if data.get('ok'):
                _LOGGER.info(
                    f'На устройстве {device.model}-{device.name} '
                    f'Изменено состояние {control.name}: {set_value}'
                )
            else:
                raise ResponseZontError(
                    f'Ошибка устройства {device.model}-{device.name}: '
                    f'{data.get("error_ui")}'
                )
        else:
            raise ResponseZontError(f'Ошибка запроса к API zont: {status}')

    return check_response


def get_icon(name_mode: str) -> str:
    for mode, icon in HEATING_MODES.items():
        if mode.lower() in name_mode.lower():
            return icon
    return 'mdi:refresh-circle'


def get_unit_sensor(type_sensor, unit_sensor) -> str:
    try:
        return VALID_UNITS[unit_sensor]
    except KeyError:
        return VALID_UNITS[type_sensor]


def get_devise_class_by_name(name: str) -> str | None:
    if 'мощн' in name.lower():
        return 'power_factor'
    elif 'влажн' in name.lower():
        return 'humidity'
    else:
        return None


def get_devise_class_sensor(sensor: SensorZONT) -> str:
    if sensor.type == 'voltage' and sensor.unit != 'В':
        if sensor.unit == '%':
            return get_devise_class_by_name(sensor.name)
        for device_class, unit in VALID_TYPE_SENSOR.items():
            if sensor.unit in unit:
                return device_class
    else:
        return sensor.type
