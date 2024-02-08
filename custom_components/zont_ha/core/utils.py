import logging
from http import HTTPStatus

from aiohttp import ClientResponse

from .exceptions import ResponseZontError

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
