import base64
import logging
import re
from http import HTTPStatus

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, URL_GET_TOKEN
from .core.exceptions import RequestAPIZONTError, InvalidMail
from .core.models_zont import ErrorZont, TokenZont
from .core.zont import Zont

_LOGGER = logging.getLogger(__name__)


async def get_token(
        hass: HomeAssistant, mail: str, login: str, password: str
) -> str:
    session = async_get_clientsession(hass)
    encoded = f'{login}:{password}'.encode("utf-8")
    basic = base64.b64encode(encoded).decode()
    headers = {
        'Authorization': f'Basic {basic}',
        'X-ZONT-Client': mail,
        'Content-Type': 'application/json'
    }
    response = await session.post(
        url=URL_GET_TOKEN,
        json={'client_name': 'Home Assistant'},
        headers=headers
    )
    text = await response.text()
    status_code = response.status
    if status_code != HTTPStatus.OK:
        error = ErrorZont.parse_raw(text)
        hass.data['error'] = error.error_ui
        raise RequestAPIZONTError(error)
    data = TokenZont.parse_raw(text)
    return data.token


async def validate_auth_token(
        hass: HomeAssistant, mail: str, token: str
) -> None:
    """Валидация токена zont"""

    zont = Zont(hass, mail, token)

    result = await zont.get_update()
    if result != HTTPStatus.OK:
        hass.data['error'] = zont.error
        raise RequestAPIZONTError


def validate_mail(mail: str) -> None:
    """Валидация почты"""

    regex = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    if not re.fullmatch(regex, mail):
        raise InvalidMail


class ZontConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2
    data: dict = None

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                validate_mail(user_input['mail'])
                if not errors:
                    self.data = user_input
                if user_input.get('get_token', False):
                    return await self.async_step_auth_pswd()
                else:
                    return await self.async_step_auth_token()
            except InvalidMail:
                _LOGGER.error(f"{user_input['mail']} - неверный формат")
                errors['base'] = 'invalid_mail'
            except Exception as e:
                _LOGGER.error(f'Что-то пошло не так, неизвестная ошибка. {e}')
                errors["base"] = "unknown"
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(schema="name"): str,
                    vol.Required(schema="mail"): str,
                    vol.Optional(schema="get_token"): bool
                }
            ),
            errors=errors
        )

    async def async_step_auth_pswd(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                token = await get_token(
                    self.hass,
                    self.data['mail'],
                    user_input['login'],
                    user_input['password']
                )
                if not errors:
                    self.data['token'] = token
                return await self.async_step_auth_token()
            except RequestAPIZONTError:
                _LOGGER.error(self.hass.data['error'])
                errors['base'] = 'invalid_auth'
            except Exception as e:
                _LOGGER.error(f'Что-то пошло не так, неизвестная ошибка. {e}')
                errors["base"] = "unknown"
        return self.async_show_form(
            step_id="auth_pswd",
            data_schema=vol.Schema(
                {
                    vol.Required("login"): str,
                    vol.Required("password"): str
                }
            ),
            errors=errors
        )

    async def async_step_auth_token(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_auth_token(
                    self.hass,
                    self.data['mail'],
                    user_input['token']
                )
                if not errors:
                    self.data.update(user_input)
                return self.async_create_entry(
                    title=self.data['name'], data=self.data
                )
            except RequestAPIZONTError:
                _LOGGER.error(self.hass.data['error'])
                errors['base'] = 'invalid_auth'
            except Exception as e:
                _LOGGER.error(f'Что-то пошло не так, неизвестная ошибка. {e}')
                errors["base"] = "unknown"
        return self.async_show_form(
            step_id="auth_token",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        schema="token", default=self.data.get('token', None)
                    ): str
                }
            ),
            errors=errors
        )
