"""Config flow for HPE iLO6 Temperatures."""
from __future__ import annotations

import ssl
import json
import base64
import urllib.request
import urllib.error
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL


def _test_connection(host: str, username: str, password: str) -> bool:
    """Try a real connection to iLO6 to validate credentials."""
    url = f"https://{host}/redfish/v1/Chassis/1/Thermal/"
    credentials = f"{username}:{password}"
    b64 = base64.b64encode(credentials.encode("ascii")).decode("ascii")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Basic {b64}",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
        return "Temperatures" in data


class HPEiLO6ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for HPE iLO6 Temperatures."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step shown in the UI."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]

            try:
                ok = await self.hass.async_add_executor_job(
                    _test_connection, host, username, password
                )
                if ok:
                    await self.async_set_unique_id(host)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"HPE iLO6 ({host})",
                        data={
                            CONF_HOST: host,
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                            CONF_SCAN_INTERVAL: user_input.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                            ),
                        },
                    )
                else:
                    errors["base"] = "cannot_connect"
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, description={"suggested_value": "192.168.0.100"}): str,
                vol.Required(CONF_USERNAME, description={"suggested_value": "administrator"}): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    int, vol.Range(min=10, max=3600)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
