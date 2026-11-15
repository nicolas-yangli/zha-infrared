# ZHA Infrared Bridge (`zha_infrared`)

A Home Assistant integration that exposes ZHA-paired Tuya / Zosung Zigbee IR blasters (such as the **TS1201**) as native Home Assistant `infrared` emitter entities (`InfraredEmitterEntity`).

## Overview

Home Assistant's native `infrared` platform allows integrations and virtual IR devices (such as climate, media player, or fan IR controllers) to transmit raw infrared commands through an `InfraredEmitterEntity`.

While ZHA (Zigbee Home Automation) supports Tuya/Zosung IR blasters via zhaquirks (exposing the Zosung IR Control cluster `0xE004`), it does not natively expose an `infrared` platform entity for them. **ZHA Infrared Bridge** bridges that gap by:

1. Creating a native `infrared` entity linked directly to your existing ZHA device.
2. Converting raw microsecond IR pulse/space timings from `InfraredCommand` into Tuya/Zosung's LZ77-compressed, Base64-encoded format.
3. Dispatching the encoded payload via `zha.issue_zigbee_cluster_command` to cluster `0xE004` (`ZosungIRControl`), command `0x02` (`IRSend`).

## Features

- **UI Config Flow**: Easily select your paired ZHA IR blaster from a dropdown list (devices matching `TS1201` are automatically prioritized at the top).
- **Native Device Attachment**: The `infrared` entity attaches directly to your existing ZHA device in the Home Assistant Device Registry.
- **Built-in Tuya LZ77 Compression**: Automatically compresses raw microsecond timing streams into the Zosung Base64 payload format expected by `TS1201` devices.
- **Modulation Frequency Handling**: Respects the command's modulation frequency (defaulting to `38000 Hz` if `<= 30000 Hz`).

## Prerequisites

1. **Home Assistant** >= 2026.4.
2. **ZHA (Zigbee Home Automation)** integration configured.
3. A **Tuya / Zosung Zigbee IR Blaster** (e.g., `TS1201` / `_TZ3290_*` / `_TYST11_*`) paired with ZHA and using a ZHA quirk that provides the `ZosungIRControl` (`0xE004`) input cluster.

## Installation

### Manual Installation

1. Copy the `custom_components/zha_infrared` directory into your Home Assistant `config/custom_components/` directory:
2. Restart Home Assistant.

### HACS (Custom Repository)

1. Open **HACS** in Home Assistant.
2. Click the three dots in the top-right corner and select **Custom repositories**.
3. Add the URL of this repository and select **Integration** as the category.
4. Install **ZHA Infrared Bridge** and restart Home Assistant.

## Configuration

1. In Home Assistant, go to **Settings** -> **Devices & services**.
2. Click **+ Add Integration** and search for **ZHA Infrared Bridge**.
3. Select your **Zigbee Device (IEEE)** from the dropdown (or enter a custom IEEE address) and specify the **Endpoint ID** (defaults to `1`).
4. Submit the form.

## What You Get & How to Use It

Once you add a ZHA IR blaster through **ZHA Infrared Bridge**:

1. **Native Infrared Entity***:
   - A new `infrared.<device_name>_infrared` entity is created.
2. **Visible Under Connectivity**:
   - Your IR blaster will appear in Home Assistant's **Infrared** panel under **Settings** -> **Devices & services** -> **Connectivity**.
3. **Use with Infrared-Dependent Integrations**:
   - Any Home Assistant integration that depends on the native `infrared` platform can now use your ZHA IR blaster as its transmitter.
   - When adding or configuring an infrared-based integration (for example, virtual IR appliance integrations for air conditioners, TVs, fans, lights, or custom IR remotes), simply select your `infrared.<device_name>_infrared` entity as the **Infrared Emitter / Transmitter**.
   - The integration will automatically pass its IR protocol commands to **ZHA Infrared Bridge**, which compresses and transmits them through your Zigbee blaster.

## How It Works

When an integration calls `async_send_command(command: InfraredCommand)` on the `ZhaTs1201InfraredEmitter` entity:

1. **Timing Extraction**: Raw pulse/space timings (in microseconds) are retrieved via `command.get_raw_timings()`.
2. **Encoding (`tuya_ir.py`)**:
   - Each timing value is clamped to `[0, 65535]` and packed as an unsigned 16-bit little-endian integer (`<H`).
   - The byte stream is compressed using Tuya's custom LZ77 sliding-window format (up to an 8192-byte window and 264-byte match length).
   - The compressed bytes are Base64-encoded into an ASCII string.
3. **Zigbee Transmission (`infrared.py`)**:
   - Calls `zha.issue_zigbee_cluster_command` targeting cluster `0xE004`, server command `0x02`, passing `code`, `freq`, and `repeats`.
