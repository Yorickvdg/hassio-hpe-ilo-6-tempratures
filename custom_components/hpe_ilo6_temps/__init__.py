"""HPE iLO6 Temperature Integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta

import urllib.request
import urllib.error
import ssl
import json
import base64

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HPE iLO6 Temperatures from a config entry."""
    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = ILO6DataCoordinator(
        hass, host, username, password, scan_interval
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class ILO6DataCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch iLO6 temperature data."""

    def __init__(self, hass, host, username, password, scan_interval):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.host = host
        self.username = username
        self.password = password

    async def _async_update_data(self):
        """Fetch data from iLO6 Redfish API."""
        try:
            data = await self.hass.async_add_executor_job(self._fetch_temperatures)
            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with iLO6 at {self.host}: {err}") from err

    def _fetch_temperatures(self):
        """Perform the actual HTTP request to iLO6 (runs in executor)."""
        url = f"https://{self.host}/redfish/v1/Chassis/1/Thermal/"

        # Build Basic Auth header — same approach as the working PowerShell script
        credentials = f"{self.username}:{self.password}"
        b64 = base64.b64encode(credentials.encode("ascii")).decode("ascii")

        # Ignore self-signed certificate (same as TrustAllCertsPolicy in PowerShell)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Basic {b64}",
                "Accept": "application/json",
                "OData-Version": "4.0",
            },
        )

        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            raw = response.read().decode("utf-8")

        payload = json.loads(raw)
        temperatures = payload.get("Temperatures", [])

        # Filter out sensors with no reading (ReadingCelsius == 0 AND no threshold set)
        # but keep sensors that genuinely read 0 if they have a threshold
        result = {}
        for sensor in temperatures:
            name = sensor.get("Name", "")
            reading = sensor.get("ReadingCelsius")
            threshold = sensor.get("UpperThresholdCritical")

            if reading is None:
                continue
            # Skip sensors that are unpopulated (reading=0 AND no critical threshold)
            if reading == 0 and not threshold:
                continue

            result[name] = {
                "reading": reading,
                "upper_threshold_critical": threshold,
                "upper_threshold_fatal": sensor.get("UpperThresholdFatal"),
                "upper_threshold_non_critical": sensor.get("UpperThresholdNonCritical"),
                "status": sensor.get("Status", {}).get("Health", "Unknown"),
            }

        return result
