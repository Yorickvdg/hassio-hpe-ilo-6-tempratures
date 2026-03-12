# HPE iLO6 Temperatures — Home Assistant Custom Component

Exposes all active temperature sensors from your HPE ProLiant server's iLO 6 interface as native Home Assistant sensor entities.

Built and validated against a **ProLiant ML350 Gen11 / iLO 6** using the working Redfish API call:
```
GET https://<ilo-ip>/redfish/v1/Chassis/1/Thermal/
Authorization: Basic <base64>
```

---

## Sensors created (based on ML350 Gen11)

| Sensor name                  | Example reading |
|------------------------------|-----------------|
| iLO6 01-Inlet Ambient        | 20 °C           |
| iLO6 02-CPU 1 PkgTmp         | 37 °C           |
| iLO6 04-P1 DIMM 1-8          | 30 °C           |
| iLO6 12-VR P1                | 44 °C           |
| iLO6 14-HD Max               | 40 °C           |
| iLO6 20-BMC                  | 61 °C           |
| iLO6 25.1-OCP 1-I/O ...      | 63 °C           |
| *(+ all other active sensors)*|                |

Sensors with `ReadingCelsius = 0` and no critical threshold (unpopulated slots like CPU2, P2 DIMMs) are automatically skipped.

---

## Installation

### Via HACS (recommended)
1. In HACS → **Integrations** → ⋮ → **Custom repositories**
2. Add this repo URL, category: **Integration**
3. Install **HPE iLO6 Temperatures**
4. Restart Home Assistant

### Manual
1. Copy the `custom_components/hpe_ilo6_temps/` folder into your HA `config/custom_components/` directory
2. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **HPE iLO6 Temperatures**
3. Enter:
   - **iLO IP address** (e.g. `192.168.0.100`)
   - **Username** (e.g. `administrator`)
   - **Password**
   - **Poll interval** in seconds (default: 60)
4. Click Submit — HA will validate the connection before saving

---

## Each sensor includes attributes

- `threshold_critical` — Upper critical threshold (°C)
- `threshold_fatal` — Upper fatal threshold (°C)  
- `threshold_warning` — Non-critical warning threshold (°C)
- `health` — iLO health status (`OK`, `Warning`, `Critical`)

---

## Notes

- Uses **Basic Auth** over HTTPS with the self-signed iLO certificate accepted (same behaviour as the iLO web UI)
- No third-party Python libraries required — uses only Python stdlib (`urllib`, `ssl`, `json`, `base64`)
- Tested on iLO 6 / Gen11; should also work on iLO 5 / Gen10
