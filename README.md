# BT Keyboard Screenshot

A one-button Bluetooth remote that takes screenshots on an iPad. Built with MicroPython on an ESP32, it advertises as a BLE HID keyboard and sends **Command + Shift + 3** when you press the trigger.

## Hardware

| Part | Typical pin (ESP32-C3) |
|------|------------------------|
| Trigger button (active high) | GPIO 5 |
| Status LED (active low) | GPIO 8 |

Adjust `TRIGGER_PIN` and `LED_PIN` in `bt_screenshot.py` if your board differs.

## Requirements

- ESP32 with BLE (e.g. ESP32-C3)
- [MicroPython](https://micropython.org/) v1.18+ with BLE support
- [MicroPythonBLEHID](https://github.com/Heerkog/MicroPythonBLEHID) — copy these onto the device filesystem:
  - `hid_services.py`
  - `hid_keystores.py`

## Setup

1. Flash MicroPython onto the ESP32.
2. Upload `bt_screenshot.py`, `hid_services.py`, and `hid_keystores.py` to the device.
3. Run the script (or rename it to `main.py` for auto-start).
4. On the iPad: **Settings → Bluetooth** and pair with **Screenshot Remote**.
5. Accept the pairing prompt if shown.

After pairing, press the button to capture a screenshot.

## Configuration

Key options in `bt_screenshot.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `DEVICE_NAME` | `"Screenshot Remote"` | BLE advertisement name |
| `TRIGGER_PIN` | `5` | Button input |
| `LED_PIN` | `8` | Status LED |
| `SLEEP_TIME_MS` | `0` | Deep sleep between triggers; `0` keeps the device awake and polling |
| `CONNECT_TIMEOUT_S` | `30` | How long to wait for an iPad connection after wake |

## How it works

1. The ESP32 boots and advertises as a BLE keyboard.
2. Once the iPad is connected, it waits for a press on the trigger pin.
3. On a debounced press, it sends the iPad external-keyboard screenshot shortcut (`⌘⇧3`).
4. Optionally it deep-sleeps until the next press (`SLEEP_TIME_MS > 0`).
