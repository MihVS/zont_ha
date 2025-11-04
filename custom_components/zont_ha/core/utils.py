import logging
from http import HTTPStatus

from aiohttp import ClientResponse

from .enums import TypeOfSensor
from .exceptions import ResponseZontError
from .models_zont_v3 import SensorZONT, DeviceZONT, ToggleButtonsZONT
from ..const import (
    HEATING_MODES, VALID_TYPE_SENSOR, ZONT_SENSOR_TYPE, UNIT_BY_TYPE,
    VALID_UNITS, BINARY_SENSOR_TYPES
)

_LOGGER = logging.getLogger(__name__)


def check_send_command(func):
    """
    Декоратор для проверки успешной отправки команды
    управления параметрами контроллера zont.
    """
    async def check_response(*args, **kwargs):
        device: DeviceZONT = kwargs.get('device')
        heating_circuit = kwargs.get('heating_circuit')
        heating_mode = kwargs.get('heating_mode')
        target_temp = kwargs.get('target_temp')
        guard_zone = kwargs.get('guard_zone')
        button = kwargs.get('button')

        command = kwargs.get('command')

        if target_temp is not None:
            control = heating_circuit
            set_value = target_temp
        elif button is not None:
            control = button
            set_value = command
        elif guard_zone is not None:
            control = guard_zone
            set_value = command
        elif heating_mode is not None:
            control = heating_mode
            set_value = 'Установлен во всех контурах'
        else:
            return func

        if isinstance(control.name, str):
            name = control.name
        else:
            name = control.name.name

        response: ClientResponse = await func(*args, **kwargs)
        status = response.status
        data = await response.json()
        if status == HTTPStatus.OK:
            _LOGGER.debug(f'Успешный запрос к API zont: {status}')
            if data.get('ok'):
                _LOGGER.info(
                    f'На устройстве "{device.device_info.model}-{device.name}" '
                    f'изменено состояние "{name}": "{set_value}"'
                )
            elif data.get('error') == 'timeout':
                _LOGGER.info(
                    f'Timeout. На устройстве {device.model}-{device.name} '
                    f'установка параметра ({name}: {set_value}) '
                    f'возможно не прошла.'
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


def get_unit_sensor(sensor: SensorZONT) -> str:
    """Фильтр для получения правильной единицы измерения сенсора"""
    type_sensor = sensor.type.value
    unit_by_type = UNIT_BY_TYPE.get(sensor.type.value)
    unit = VALID_UNITS.get(sensor.unit)
    if type_sensor == 'voltage':
        return unit
    if isinstance(
        unit, type(unit_by_type)
    ):
        return unit
    else:
        return UNIT_BY_TYPE.get(type_sensor, unit)


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
        return ZONT_SENSOR_TYPE.get(sensor.type.value, sensor.type.value)


def validate_value_sensor(
        value_new: str | float, value_old: str | float
) -> str | float:
    try:
        if abs(value_new) < (abs(value_old) + 1) * 100:
            return value_new
        else:
            return value_old
    except TypeError:
        return value_new

def is_binary_sensor(sensor: SensorZONT) -> bool:
    if sensor.type.value in BINARY_SENSOR_TYPES:
        return True
    if sensor.type == TypeOfSensor.OTHER and sensor.triggered is not None:
        return True
    return False

