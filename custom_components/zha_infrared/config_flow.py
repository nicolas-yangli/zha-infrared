"""Config flow for ZHA Infrared Bridge."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CONF_ENDPOINT_ID, CONF_IEEE, DEFAULT_ENDPOINT_ID, DOMAIN


def _get_zha_devices(hass_dr: dr.DeviceRegistry) -> dict[str, str]:
    """Return a mapping of ZHA IEEE address -> display label."""
    devices: dict[str, str] = {}
    for device in hass_dr.devices:
        for domain, identifier in device.identifiers:
            if domain == "zha":
                label = device.name_by_user or device.name or identifier
                if device.model:
                    label = f"{label} ({device.model}) [{identifier}]"
                else:
                    label = f"{label} [{identifier}]"
                devices[identifier] = label
    return devices


class ZhaInfraredConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ZHA Infrared Bridge."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        dev_reg = dr.async_get(self.hass)
        zha_devices = _get_zha_devices(dev_reg)

        if user_input is not None:
            ieee = user_input[CONF_IEEE].strip()
            endpoint_id = int(user_input[CONF_ENDPOINT_ID])
            await self.async_set_unique_id(f"{ieee}_{endpoint_id}")
            self._abort_if_unique_id_configured()

            title = zha_devices.get(ieee, ieee)
            return self.async_create_entry(
                title=title,
                data={
                    CONF_IEEE: ieee,
                    CONF_ENDPOINT_ID: endpoint_id,
                    CONF_NAME: title,
                },
            )

        if zha_devices:
            options = [
                SelectOptionDict(value=ieee, label=label)
                for ieee, label in sorted(
                    zha_devices.items(),
                    key=lambda item: ("TS1201" not in item[1], item[1]),
                )
            ]
            ieee_schema: Any = SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    mode=SelectSelectorMode.DROPDOWN,
                    custom_value=True,
                )
            )
        else:
            ieee_schema = str

        schema = vol.Schema(
            {
                vol.Required(CONF_IEEE): ieee_schema,
                vol.Required(
                    CONF_ENDPOINT_ID, default=DEFAULT_ENDPOINT_ID
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=240,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
