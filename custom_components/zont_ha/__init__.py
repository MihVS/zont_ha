import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, ZONT
from .core.zont import Zont

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    # _LOGGER.warning(config_entry.data)
    entry_id = config_entry.entry_id
    email = config_entry.data.get("mail")
    token = config_entry.data.get("token")
    zont = Zont(hass, email, token)
    await zont.get_update()

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry_id] = zont
    await hass.config_entries.async_forward_entry_setups(
        config_entry, ['sensor']
    )
    return True
