import logging
import sys

import voluptuous as vol

from homeassistant import config_entries
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_LOGGER.warning(sys.version)


class ZontConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            _LOGGER.debug(user_input)
            return self.async_create_entry(title=DOMAIN, data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("mail"): str,
                    vol.Required("token"): str
                }
            )
        )

