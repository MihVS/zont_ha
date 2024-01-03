import logging
import re

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .core.zont import Zont
from .core.exceptions import RequestAPIZONTError, InvalidMail

_LOGGER = logging.getLogger(__name__)


async def validate_auth(hass: HomeAssistant, mail: str, token: str) -> None:
    """Валидация токена zont"""

    zont = Zont(hass, mail, token)

    result = await zont.get_update()
    _LOGGER.debug(f'validate_auth: {result}')
    if result != 200:
        hass.data['error'] = zont.error
        raise RequestAPIZONTError


def validate_mail(mail: str) -> None:
    """Валидация почты"""

    regex = re.compile(
        r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+'
    )

    if not re.fullmatch(regex, mail):
        raise InvalidMail


class ZontConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                _LOGGER.debug(user_input)
                validate_mail(user_input['mail'])
                await validate_auth(
                    self.hass,
                    user_input['mail'], user_input['token']
                )
                return self.async_create_entry(
                    title=user_input['name'], data=user_input
                )
            except InvalidMail:
                _LOGGER.error(f"{user_input['mail']} - неверный формат")
                errors['base'] = 'invalid_mail'
            except RequestAPIZONTError:
                _LOGGER.error(self.hass.data['error'])
                errors['base'] = 'invalid_auth'
            except Exception as e:
                _LOGGER.error(f'Что-то пошло не так, неизвестная ошибка. {e}')
                errors["base"] = "unknown"
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required("mail"): str,
                    vol.Required("token"): str
                }
            ),
            errors=errors
        )
