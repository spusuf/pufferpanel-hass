import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.core import callback
from .const import DOMAIN

class PufferPanelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PufferPanel."""

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title=user_input["host"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Required("port", default=8080): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=65535, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required("client_id"): str,
                vol.Required("client_secret"): str,
                vol.Optional("use_https", default=False): selector.BooleanSelector(),
                vol.Required("refresh_frequency", default=60): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=15, max=3600, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="sec")
                ),
                vol.Required("core_count", default=1): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=512, mode=selector.NumberSelectorMode.BOX)
                ),
            }),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input=None):
        """Handle reconfiguration."""
        errors = {}
        config_entry = self._get_reconfigure_entry()
        if user_input is not None:
            return self.async_update_reload_and_abort(
                config_entry,
                data={**config_entry.data, **user_input},
                reason="reconfigure_successful",
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required("host", default=config_entry.data.get("host")): selector.TextSelector(),
                vol.Required("port", default=config_entry.data.get("port", 8080)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=65535, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required("client_id", default=config_entry.data.get("client_id")): selector.TextSelector(),
                vol.Required("client_secret", default=config_entry.data.get("client_secret")): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Optional("use_https", default=config_entry.data.get("use_https", False)): selector.BooleanSelector(),
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return PufferPanelOptionsFlow(config_entry)

class PufferPanelOptionsFlow(config_entries.OptionsFlow):
    """Handle options for PufferPanel."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema({
            vol.Required("refresh_frequency"): selector.NumberSelector(
                selector.NumberSelectorConfig(min=15, max=3600, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="sec")
            ),
            vol.Required("core_count"): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=512, mode=selector.NumberSelectorMode.BOX)
            ),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                data_schema,
                self._config_entry.options or self._config_entry.data
            ),
        )
