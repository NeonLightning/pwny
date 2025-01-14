# Plugins Configuration Guide

---

## **weather2pwn Plugin**

The `weather2pwn` plugin retrieves weather data and displays it based on GPS coordinates or a predefined city ID. It integrates with OpenWeatherMap and requires an API key for data retrieval.

### Configuration Options

| Configuration Key                        | Description                                                                                  |
|------------------------------------------|----------------------------------------------------------------------------------------------|
| `main.plugins.weather2pwn.log`           | Enable or disable logging of weather data. (`true` or `false`)                              |
| `main.plugins.weather2pwn.gps_loc`       | Set the GPS device location (e.g., `/dev/ttyACM0`).                                          |
| `main.plugins.weather2pwn.cityid`        | Set the City ID from OpenWeatherMap.                                                        |
| `main.plugins.weather2pwn.getbycity`     | Choose whether to retrieve weather data by GPS or City ID. (`true` or `false`)              |
| `main.plugins.weather2pwn.api_key`       | Your OpenWeatherMap API key. Obtain it from [OpenWeatherMap](https://openweathermap.org/).  |
| `main.plugins.weather2pwn.decimal`       | Display temperatures with two decimal places. (`true` or `false`)                          |
| `main.plugins.weather2pwn.units`         | Set temperature units to Celsius (`c`) or Fahrenheit (`f`).                                 |
| `main.plugins.weather2pwn.displays`      | Choose which values to display (e.g., `"city", "temp", "sky"`).                           |

### Notes
- GPS functionality requires `gpsdeasy`. Install it before enabling GPS-based weather updates.
- If GPS is unavailable, the plugin falls back to the predefined City ID.

### Getting Started with OpenWeatherMap
1. Visit [OpenWeatherMap](https://openweathermap.org/).
2. Create an account and obtain your API key.
3. Search for your city and note the City ID.
---

## **sorted-password-list Plugin**

The `sorted-password-list` plugin organizes and displays passwords, with additional features such as QR code generation and field customization.

### Configuration Options

| Configuration Key                                       | Description                                                                                   |
|---------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `main.plugins.sorted-password-list.show_number`         | Show the number of unique passwords. (`true` or `false`)                                      |
| `main.plugins.sorted-password-list.keep_qr`             | Keep the generated QR files in `/home/pi/qrcodes/`. (`true` or `false`)                       |
| `main.plugins.sorted-password-list.fields`              | Limit displayed fields(e.g., `['ssid', 'bssid', 'password', 'origin', 'gps', 'strength']`).        |
| `main.plugins.sorted-password-list.position`            | Set custom display position using X and Y coordinates (e.g., `"0,93"`).                     |
| `main.plugins.sorted-password-list.qr_display`          | Enable or disable QR code display for each password. (`true` or `false`)                     |

### Requirements
- **QR Code Generation**: Install the required library using the following command:
  ```bash
  sudo apt install python3-qrcode
  ```
- The plugin saves generated QR codes to `/home/pi/qrcodes/` when `keep_qr` is enabled.

---

## **internet-conection**
A plugin to display if your Pwnagotchi is connected to the internet.

---

## **bt-logger**
Logs all seen Bluetooth devices and optionally includes GPS coordinates.

### Configuration Options
| Configuration Key                     | Description                                                                   |
|---------------------------------------|-------------------------------------------------------------------------------|
| `main.plugins.bt-logger.gps`          | Include GPS coordinates with the device name and MAC. (`true` or `false`)    |
| `main.plugins.bt-logger.id_only`      | Exclude hidden devices. (`true` or `false`)                                  |
| `main.plugins.bt-logger.display`      | Display the number of found devices on the screen. (`true` or `false`)       |

### Notes
- GPS functionality requires the `gpsdeasy` library. Ensure it is installed.

---

## **IPDisplay**
Displays your IP addresses on the Pwnagotchi screen.

### Configuration Options
| Configuration Key                             | Description                                                                 |
|-----------------------------------------------|-----------------------------------------------------------------------------|
| `main.plugins.IPDisplay.skip_devices`         | A list of devices to exclude from display (e.g., `'eth0', 'usb0', 'wlan0'`). |
| `main.plugins.IPDisplay.delay_time`           | Time in seconds between switching the displayed device.                     |

---

## **webssh**
Provides a web-based SSH client for accessing your system directly from a browser.

---

## **binary**
Displays a binary clock on the Pwnagotchi screen.

### Configuration Options
| Configuration Key                       | Description                                                                 |
|-----------------------------------------|-----------------------------------------------------------------------------|
| `main.plugins.binary.format`            | Format for the clock display (e.g., `"%H:%M"` for hours and minutes).       |
| `main.plugins.binary.digits`            | Number of digits to display. Default is 8.                                 |

---

## **uncracked**
Displays and allows the download of captures not found in the `wpa-sec.potfile`.

---

## **fluxmod**
Switches between inverted and non-inverted modes on a timer.

### Configuration Options
| Configuration Key                         | Description                                                                 |
|-------------------------------------------|-----------------------------------------------------------------------------|
| `main.plugins.fluxmod.invert_on_time`     | Time to enable inverted mode (e.g., `"20:00"`).                             |
| `main.plugins.fluxmod.invert_off_time`    | Time to disable inverted mode (e.g., `"6:00"`).                             |

---

## **clock**
A simple plugin to display the time and date on the Pwnagotchi screen as separate labels.

---