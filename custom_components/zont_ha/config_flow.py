import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .core.zont import Zont
from .core.exceptions import RequestAPIZONTError

_LOGGER = logging.getLogger(__name__)


async def validate_auth(hass: HomeAssistant, mail: str, token: str) -> None:
    """Валидация токена zont"""

    zont = Zont(hass, mail, token)

    result = await zont.get_update()
    _LOGGER.debug(f'validate_auth: {result}')
    if result != 200:
        hass.data['error'] = zont.error
        raise RequestAPIZONTError


class ZontConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                _LOGGER.debug(user_input)
                await validate_auth(
                    self.hass, user_input['mail'], user_input['token']
                )
                return self.async_create_entry(title=DOMAIN, data=user_input)
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
                    vol.Required("mail"): str,
                    vol.Required("token"): str
                }
            ),
            errors=errors
        )
