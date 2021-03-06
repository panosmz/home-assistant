"""Support for wake on lan."""
import logging
import platform
import subprocess as sp

import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchDevice
from homeassistant.const import CONF_HOST, CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.script import Script

_LOGGER = logging.getLogger(__name__)

CONF_BROADCAST_ADDRESS = 'broadcast_address'
CONF_MAC_ADDRESS = 'mac_address'
CONF_OFF_ACTION = 'turn_off'

DEFAULT_NAME = 'Wake on LAN'
DEFAULT_PING_TIMEOUT = 1

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC_ADDRESS): cv.string,
    vol.Optional(CONF_BROADCAST_ADDRESS): cv.string,
    vol.Optional(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_OFF_ACTION): cv.SCRIPT_SCHEMA,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up a wake on lan switch."""
    broadcast_address = config.get(CONF_BROADCAST_ADDRESS)
    host = config.get(CONF_HOST)
    mac_address = config.get(CONF_MAC_ADDRESS)
    name = config.get(CONF_NAME)
    off_action = config.get(CONF_OFF_ACTION)

    add_entities([WOLSwitch(
        hass, name, host, mac_address, off_action, broadcast_address)], True)


class WOLSwitch(SwitchDevice):
    """Representation of a wake on lan switch."""

    def __init__(
            self, hass, name, host, mac_address, off_action,
            broadcast_address):
        """Initialize the WOL switch."""
        import wakeonlan
        self._hass = hass
        self._name = name
        self._host = host
        self._mac_address = mac_address
        self._broadcast_address = broadcast_address
        self._off_script = Script(hass, off_action) if off_action else None
        self._state = False
        self._wol = wakeonlan

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    def turn_on(self, **kwargs):
        """Turn the device on."""
        if self._broadcast_address:
            self._wol.send_magic_packet(
                self._mac_address, ip_address=self._broadcast_address)
        else:
            self._wol.send_magic_packet(self._mac_address)

    def turn_off(self, **kwargs):
        """Turn the device off if an off action is present."""
        if self._off_script is not None:
            self._off_script.run()

    def update(self):
        """Check if device is on and update the state."""
        if platform.system().lower() == 'windows':
            ping_cmd = ['ping', '-n', '1', '-w',
                        str(DEFAULT_PING_TIMEOUT * 1000), str(self._host)]
        else:
            ping_cmd = ['ping', '-c', '1', '-W',
                        str(DEFAULT_PING_TIMEOUT), str(self._host)]

        status = sp.call(ping_cmd, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
        self._state = not bool(status)
