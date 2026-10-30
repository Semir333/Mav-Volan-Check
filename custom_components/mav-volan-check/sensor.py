"""Sensor platform for BKK & MÁV Transit Sync."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_TRANSPORT_TYPE, TRANSPORT_TYPE_TRAIN

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up transit sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TransitSensor(coordinator, entry)])


class TransitSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Transit Sensor."""

    def __init__(self, coordinator, entry):
        """Initialize sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self.transport_type = entry.data.get(CONF_TRANSPORT_TYPE)
        
        self._attr_name = entry.title
        self._attr_unique_id = f"{entry.entry_id}_transit_sensor"
        
        if self.transport_type == TRANSPORT_TYPE_TRAIN:
            self._attr_icon = "mdi:train"
        else:
            self._attr_icon = "mdi:bus"

    @property
    def native_value(self):
        """Return the main state (departure time)."""
        if self.coordinator.data:
            return self.coordinator.data.get("departure", "N/A")
        return "Betöltés..."

    @property
    def extra_state_attributes(self):
        """Return extra state attributes for Lovelace cards."""
        if not self.coordinator.data:
            return {}

        data = self.coordinator.data

        if self.transport_type == TRANSPORT_TYPE_TRAIN:
            return {
                "delay": data.get("delay", 0),
                "scheduled": data.get("scheduled", "N/A"),
                "train_no": data.get("train_no", "N/A"),
                "last_update": data.get("last_update", ""),
            }
        else:
            return {
                "delay": data.get("delay", 0),
                "route": data.get("route", "-"),
                "headsign": data.get("headsign", ""),
                "entry": data.get("raw_entry", {}),
                "references": data.get("raw_references", {}),
            }