from .const import DOMAIN
from homeassistant import config_entries
import voluptuous as vol


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            pass
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("password"): str})
        )
