import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .core.zont import Zont

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.warning(entry.data)
    email = entry.data.get("mail")
    token = entry.data.get("token")
    zont = Zont(hass, email, token)
    await zont.get_update()

    hass.data.setdefault(DOMAIN, {})
    _LOGGER.warning(hass.data[DOMAIN])

    account_id = len(hass.data[DOMAIN])
    hass.data[DOMAIN].setdefault(account_id, {})
    _LOGGER.debug(f'Create account ID: {account_id}')

    for device in zont.data.devices:
        hass.data[DOMAIN][account_id][f'{device.id}'] = device
    _LOGGER.debug(f'Number of device: {len(hass.data[DOMAIN][account_id])}')
    await hass.config_entries.async_forward_entry_setups(entry, ['sensor'])
    return True
