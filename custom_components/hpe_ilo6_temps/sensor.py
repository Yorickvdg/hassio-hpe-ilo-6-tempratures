"""Sensor platform for HPE iLO6 Temperatures."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HPE iLO6 temperature sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    host = entry.data[CONF_HOST]

    # Wait for first data, then create one entity per sensor
    entities = [
        ILO6TemperatureSensor(coordinator, host, sensor_name)
        for sensor_name in coordinator.data
    ]

    async_add_entities(entities, update_before_add=True)


class ILO6TemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of a single iLO6 temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, host: str, sensor_name: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_name = sensor_name
        self._host = host

        # Unique ID: domain + host + sensor name (slugified)
        slug = sensor_name.lower().replace(" ", "_").replace("-", "_")
        self._attr_unique_id = f"hpe_ilo6_{host}_{slug}"

        # Friendly name shown in HA
        self._attr_name = f"iLO6 {sensor_name}"

        # Group all sensors under one device per iLO host
        self._attr_device_info = {
            "identifiers": {(DOMAIN, host)},
            "name": f"HPE iLO6 ({host})",
            "manufacturer": "Hewlett Packard Enterprise",
            "model": "ProLiant iLO 6",
            "configuration_url": f"https://{host}",
        }

    @property
    def native_value(self):
        """Return current temperature reading."""
        if self.coordinator.data is None:
            return None
        sensor = self.coordinator.data.get(self._sensor_name)
        if sensor is None:
            return None
        return sensor["reading"]

    @property
    def extra_state_attributes(self):
        """Return additional sensor attributes."""
        if self.coordinator.data is None:
            return {}
        sensor = self.coordinator.data.get(self._sensor_name, {})
        attrs = {}
        if sensor.get("upper_threshold_critical") is not None:
            attrs["threshold_critical"] = sensor["upper_threshold_critical"]
        if sensor.get("upper_threshold_fatal") is not None:
            attrs["threshold_fatal"] = sensor["upper_threshold_fatal"]
        if sensor.get("upper_threshold_non_critical") is not None:
            attrs["threshold_warning"] = sensor["upper_threshold_non_critical"]
        if sensor.get("status"):
            attrs["health"] = sensor["status"]
        return attrs

    @property
    def icon(self):
        """Return icon based on temperature relative to threshold."""
        if self.coordinator.data is None:
            return "mdi:thermometer"
        sensor = self.coordinator.data.get(self._sensor_name, {})
        reading = sensor.get("reading", 0)
        threshold = sensor.get("upper_threshold_critical")
        if threshold and reading >= threshold * 0.9:
            return "mdi:thermometer-alert"
        if reading > 60:
            return "mdi:thermometer-high"
        return "mdi:thermometer"
