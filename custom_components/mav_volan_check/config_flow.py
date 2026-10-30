"""Config flow for BKK & MÁV Transit Sync integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_TRANSPORT_TYPE,
    CONF_STOP_ID,
    CONF_DIRECTION_FILTER,
    CONF_API_KEY,
    CONF_SCAN_INTERVAL,
    TRANSPORT_TYPE_TRAIN,
    TRANSPORT_TYPE_BUS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_BKK_KEY,
)

class TransitConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BKK & MÁV Transit Sync."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            title = f"{user_input['name']} ({'Vonat' if user_input[CONF_TRANSPORT_TYPE] == TRANSPORT_TYPE_TRAIN else 'Busz'})"
            return self.async_create_entry(title=title, data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required("name", default="Erdőkertes Transit"): str,
                vol.Required(CONF_TRANSPORT_TYPE, default=TRANSPORT_TYPE_TRAIN): vol.In(
                    {
                        TRANSPORT_TYPE_TRAIN: "Vonat (Traintrack API)",
                        TRANSPORT_TYPE_BUS: "Busz (BKK OTP API)",
                    }
                ),
                vol.Optional(CONF_DIRECTION_FILTER, default="nyugati"): str,
                vol.Optional(CONF_STOP_ID, default="volan_777764_2"): str,
                vol.Optional(CONF_API_KEY, default=DEFAULT_BKK_KEY): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TransitOptionsFlowHandler(config_entry)


class TransitOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for changing settings later."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        data = self.config_entry.data

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_DIRECTION_FILTER,
                    default=options.get(CONF_DIRECTION_FILTER, data.get(CONF_DIRECTION_FILTER, "nyugati")),
                ): str,
                vol.Optional(
                    CONF_STOP_ID,
                    default=options.get(CONF_STOP_ID, data.get(CONF_STOP_ID, "volan_777764_2")),
                ): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
                ): cv.positive_int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)