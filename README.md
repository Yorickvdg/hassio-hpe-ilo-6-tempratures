# HPE iLO6 Temperatures — Home Assistant Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2023.x%2B-blue.svg)](https://www.home-assistant.io/)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

A **zero-dependency** Home Assistant custom integration that exposes all active temperature sensors from an **HPE ProLiant server's iLO 6** interface as native HA sensor entities — including per-sensor critical thresholds and iLO health status.

Developed and validated against a **ProLiant ML350 Gen11 running iLO 6**.

---

## Features

- 🌡️ **All active temperature sensors** auto-discovered from the Redfish API
- ⚠️ **Threshold attributes** — critical, fatal, and warning values per sensor
- 🏥 **iLO health status** — `OK`, `Warning`, or `Critical` per sensor
- 🔄 **Configurable poll interval** (default: 60 seconds)
- 🖥️ **UI-based setup** — no YAML editing required
- 📦 **No external Python libraries** — uses only stdlib (`urllib`, `ssl`, `json`, `base64`)
- 🔒 Accepts iLO's self-signed certificate automatically (same behaviour as the iLO web UI)

---

## Sensors

All sensors are grouped under a single **device** per iLO host in Home Assistant.

Sensors with `ReadingCelsius = 0` and no defined threshold (unpopulated CPU/DIMM slots) are automatically skipped. The following sensors were confirmed active on a ProLiant ML350 Gen11:

| Sensor | Example reading | Critical threshold |
|---|---|---|
| 01-Inlet Ambient | 20 °C | 42 °C |
| 02-CPU 1 PkgTmp | 37 °C | 90 °C |
| 04-P1 DIMM 1-8 | 30 °C | 92 °C |
| 06-P1 DIMM 9-16 | 36 °C | 92 °C |
| 12-VR P1 | 44 °C | 110 °C |
| 14-HD Max | 40 °C | 72 °C |
| 18-Stor Batt | 26 °C | 60 °C |
| 19-Chipset | 40 °C | 100 °C |
| 20-BMC | 61 °C | 110 °C |
| 21-P/S 1 Inlet | 32 °C | — |
| 22-P/S 1 | 40 °C | — |
| 49-Board Inlet | 29 °C | 90 °C |
| 50-Sys Exhaust 2 | 31 °C | 90 °C |
| 52-Sys Exhaust 1 | 36 °C | 90 °C |
| 77-CPU 1 | 40 °C | 70 °C |
| 25.1-OCP 1-I/O controller | 63 °C | 110 °C |
| 27.1-OCP 2-Communication Channel | 62 °C | 110 °C |

Your server may expose additional or different sensors — all active sensors are created automatically.

---

## Requirements

- Home Assistant **2023.1** or newer
- HPE iLO 6 (**iLO Standard license** is sufficient — no Advanced license required)
- Network access from HA to the iLO management IP on port **443**
- An iLO user account with at least **Read** privileges

---

## Installation

### Via HACS (recommended)

1. Open **HACS → Integrations**
2. Click the **⋮** menu → **Custom repositories**
3. Add this repository URL and select category **Integration**
4. Install **HPE iLO6 Temperatures**
5. Restart Home Assistant

### Manual

1. Download or clone this repository
2. Copy the `custom_components/hpe_ilo6_temps/` folder into your HA configuration directory:
   ```
   config/custom_components/hpe_ilo6_temps/
   ```
3. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **HPE iLO6 Temperatures**
3. Fill in the form:

   | Field | Example |
   |---|---|
   | iLO IP address or hostname | `192.168.0.100` |
   | Username | `administrator` |
   | Password | `••••••••` |
   | Poll interval (seconds) | `60` |

4. Click **Submit** — the integration validates the connection before saving

HA will immediately create one sensor entity per active temperature sensor.

---

## How it works

The integration queries the **Redfish REST API** built into iLO 6:

```
GET https://<ilo-ip>/redfish/v1/Chassis/1/Thermal/
Authorization: Basic <base64(user:pass)>
```

This is the same API endpoint accessible directly in a browser or via PowerShell — validated before building this integration:

```powershell
$base64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("administrator:password"))
$headers = @{ Authorization = "Basic $base64" }
Invoke-RestMethod -Uri "https://192.168.0.100/redfish/v1/Chassis/1/Thermal/" -Headers $headers
```

Data is fetched on a configurable interval using a `DataUpdateCoordinator`, keeping all sensors in sync with a single API call per poll cycle.

---

## Sensor attributes

Each entity exposes the following additional attributes (where available):

| Attribute | Description |
|---|---|
| `threshold_critical` | Upper critical threshold in °C |
| `threshold_fatal` | Upper fatal threshold in °C |
| `threshold_warning` | Non-critical warning threshold in °C |
| `health` | iLO health status (`OK` / `Warning` / `Critical`) |

---

## Compatibility

| Server generation | iLO version | Status |
|---|---|---|
| Gen11 (ML350, DL360, etc.) | iLO 6 | ✅ Tested |
| Gen10 / Gen10 Plus | iLO 5 | 🟡 Should work (same Redfish path) |
| Gen9 and older | iLO 4 | ❌ Not supported (different API) |

---

## Troubleshooting

**Cannot connect**
- Verify the iLO IP is reachable from your HA host (`ping` / browser test)
- Confirm port 443 is not blocked by a firewall

**401 Unauthorized**
- Double-check username and password
- Ensure the iLO account has not expired or been locked

**Sensors show 0 or are missing**
- Unpopulated hardware slots (empty CPU sockets, absent DIMMs) correctly return 0 and are filtered out
- Check HA logs under **Settings → System → Logs** and filter for `hpe_ilo6`

**`-SkipCertificateCheck` errors (not an integration issue)**
- This only applies when testing manually in Windows PowerShell 5.1 — the integration handles certificate trust internally

---

## License

MIT — see [LICENSE](LICENSE) for details.
