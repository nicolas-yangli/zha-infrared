"""Infrared emitter platform for ZHA TS1201 / Zosung IR blasters."""

from __future__ import annotations

import logging

from homeassistant.components.infrared import InfraredCommand, InfraredEmitterEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ENDPOINT_ID,
    CONF_IEEE,
    DEFAULT_ENDPOINT_ID,
    DEFAULT_IR_FREQUENCY,
    MIN_IR_FREQUENCY,
    ZOSUNG_CMD_IR_SEND,
    ZOSUNG_IR_CONTROL_CLUSTER,
)
from .tuya_ir import encode_timings

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ZHA Infrared emitter entity from a config entry."""
    ieee: str = entry.data[CONF_IEEE]
    endpoint_id: int = entry.data.get(CONF_ENDPOINT_ID, DEFAULT_ENDPOINT_ID)
    async_add_entities([ZhaTs1201InfraredEmitter(ieee, endpoint_id)])


class ZhaTs1201InfraredEmitter(InfraredEmitterEntity):
    """Native Home Assistant infrared emitter backed by a ZHA TS1201 blaster."""

    _attr_has_entity_name = True
    _attr_name = "Infrared"

    def __init__(self, ieee: str, endpoint_id: int) -> None:
        """Initialize the ZHA TS1201 infrared emitter."""
        self._ieee = ieee
        self._endpoint_id = endpoint_id
        self._attr_unique_id = f"{ieee}_{endpoint_id}_infrared"
        self._attr_device_info = DeviceInfo(identifiers={("zha", ieee)})

    async def async_send_command(self, command: InfraredCommand) -> None:
        """Send an IR command via ZHA ZosungIRControl IRSend."""
        timings = [abs(t) for t in command.get_raw_timings()]
        encoded_code = encode_timings(timings)

        freq = command.modulation
        if freq <= MIN_IR_FREQUENCY:
            freq = DEFAULT_IR_FREQUENCY

        _LOGGER.debug(
            "Sending IR command to %s (ep=%s, freq=%s, repeats=%s, len=%s)",
            self._ieee,
            self._endpoint_id,
            freq,
            command.repeat_count,
            len(encoded_code),
        )

        await self.hass.services.async_call(
            "zha",
            "issue_zigbee_cluster_command",
            {
                "ieee": self._ieee,
                "endpoint_id": self._endpoint_id,
                "cluster_id": ZOSUNG_IR_CONTROL_CLUSTER,
                "cluster_type": "in",
                "command": ZOSUNG_CMD_IR_SEND,
                "command_type": "server",
                "params": {
                    "code": encoded_code,
                    "freq": freq,
                    "repeats": command.repeat_count,
                },
            },
            blocking=True,
        )
