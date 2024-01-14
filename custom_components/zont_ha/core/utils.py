import logging
from http import HTTPStatus

from aiohttp import ClientResponse

from config.custom_components.zont_ha.core.exceptions import ResponseZontError

_LOGGER = logging.getLogger(__name__)


def check_send_command(func):
    """
    Декоратор для проверки успешной отправки команды
    управления параметрами контроллера zont.
    """
    async def check_response(*args, **kwargs):
        device = kwargs.get('device')
        heating_circuit = kwargs.get('heating_circuit')
        target_temp = kwargs.get('target_temp')

        control = heating_circuit

        # length = len(args)
        # if length == 3:
        #     device, control, target_state = args
        # elif length == 2:
        #     device, control = args
        # else:
        #     return func
        response: ClientResponse = await func(*args, **kwargs)
        # _target_state = (
        #     lambda: str(target_state) if (length == 3) else 'toggle'
        # )
        status = response.status
        data = await response.json()
        if status == HTTPStatus.OK:
            _LOGGER.debug(f'Успешный запрос к API zont: {status}')
            if data.get('ok'):
                _LOGGER.info(
                    f'На устройстве {device.model}-{device.name} '
                    f'Изменено состояние {control.name}: {target_temp}'
                )
            else:
                raise ResponseZontError(
                    f'Ошибка устройства {device.model}-{device.name}: '
                    f'{data.get("error_ui")}'
                )
        else:
            raise ResponseZontError(f'Ошибка запроса к API zont: {status}')

    return check_response
