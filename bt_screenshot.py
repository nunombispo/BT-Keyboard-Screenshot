# MicroPython BLE screenshot remote for iPad
#
# Dependencies (copy onto the ESP32 filesystem):
#   https://github.com/Heerkog/MicroPythonBLEHID
#     - hid_services.py
#     - hid_keystores.py
#
# First-time iPad pairing:
#   1. Upload this script plus the two library files above.
#   2. Run the script; the ESP32 advertises as DEVICE_NAME.
#   3. On iPad: Settings → Bluetooth → pair with the device.
#   4. Accept the pairing request if prompted.
#
# iPad screenshot shortcut (external keyboard): Command + Shift + 3

from machine import Pin, deepsleep
from time import sleep, ticks_ms, ticks_diff
import esp32

from hid_services import Keyboard
from hid_keystores import NVSKeyStore

# -------------------------
# CONFIGURATION
# -------------------------
DEVICE_NAME = "Screenshot Remote"

TRIGGER_PIN = 5          # Button input (active high with internal pull-down)
LED_PIN = 8              # LED (active low on many ESP32-C3 boards)

# Deep sleep between triggers (set to 0 to stay awake and poll pin 5)
SLEEP_TIME_MS = 0

# How long to advertise / wait for iPad connection after wake
CONNECT_TIMEOUT_S = 30

# Debounce for the trigger button
DEBOUNCE_MS = 50

# iPad screenshot: Command + Shift + 3
# HID usage for "3" is 0x20
SCREENSHOT_KEY = 0x20


# -------------------------
# HARDWARE
# -------------------------
led = Pin(LED_PIN, Pin.OUT)
trigger = Pin(TRIGGER_PIN, Pin.IN, Pin.PULL_DOWN)


# -------------------------
# BLE KEYBOARD
# -------------------------
keyboard = Keyboard(DEVICE_NAME)
keyboard.set_keystore(NVSKeyStore())
keyboard.start()


def led_on():
    led.value(0)


def led_off():
    led.value(1)


def is_trigger_pressed():
    return trigger.value() == 1


def wait_for_trigger(timeout_s=60):
    """Block until the button on pin 5 is pressed (with debounce)."""
    deadline = ticks_ms() + timeout_s * 1000
    while ticks_diff(deadline, ticks_ms()) > 0:
        if is_trigger_pressed():
            led_on()
            sleep(DEBOUNCE_MS / 1000)
            if is_trigger_pressed():
                return True
            led_off()
        else:
            led_off()
        sleep(0.05)
    led_off()
    return False


def handle_trigger():
    """Detect a debounced press, light the LED, send screenshot, then turn LED off."""
    if not is_trigger_pressed():
        return False

    led_on()
    sleep(DEBOUNCE_MS / 1000)
    if not is_trigger_pressed():
        led_off()
        return False

    print("Trigger pressed.")
    send_screenshot()
    print("Screenshot sent.")

    while is_trigger_pressed():
        sleep(0.05)

    led_off()
    sleep(0.3)
    return True


def wait_for_connection(timeout_s=CONNECT_TIMEOUT_S):
    """Advertise until the iPad connects or timeout expires."""
    if keyboard.get_state() is Keyboard.DEVICE_CONNECTED:
        return True

    if keyboard.get_state() is Keyboard.DEVICE_IDLE:
        keyboard.start_advertising()

    deadline = ticks_ms() + timeout_s * 1000
    while ticks_diff(deadline, ticks_ms()) > 0:
        if keyboard.get_state() is Keyboard.DEVICE_CONNECTED:
            return True
        sleep(0.2)

    if keyboard.get_state() is Keyboard.DEVICE_ADVERTISING:
        keyboard.stop_advertising()

    return keyboard.get_state() is Keyboard.DEVICE_CONNECTED


def send_screenshot():
    """Send Command + Shift + 3 to the paired iPad."""
    keyboard.set_modifiers(left_gui=1, left_shift=1)
    keyboard.set_keys(SCREENSHOT_KEY)
    keyboard.notify_hid_report()
    sleep(0.08)

    keyboard.set_keys()
    keyboard.set_modifiers()
    keyboard.notify_hid_report()
    sleep(0.05)


def configure_wake_on_trigger():
    """Wake from deep sleep when pin 5 goes high."""
    esp32.wake_on_ext0(trigger, esp32.WAKEUP_ALL_HIGH)


def go_to_sleep():
    if SLEEP_TIME_MS <= 0:
        return

    print("Sleeping...")
    configure_wake_on_trigger()
    led_off()
    deepsleep(SLEEP_TIME_MS)


# -------------------------
# MAIN LOGIC
# -------------------------
def main():
    try:
        print("Wake-up:", DEVICE_NAME)
        led_off()

        # Allow BLE stack to settle after boot
        sleep(1)

        if not wait_for_connection():
            print("iPad not connected within timeout.")
            go_to_sleep()
            return

        print("Connected to iPad.")

        # If we woke from deep sleep on the button, fire immediately.
        # Otherwise wait for a press (continuous mode when SLEEP_TIME_MS = 0).
        if SLEEP_TIME_MS > 0 and is_trigger_pressed():
            handle_trigger()
            go_to_sleep()
            return

        if SLEEP_TIME_MS <= 0:
            print("Waiting for trigger on pin", TRIGGER_PIN, "...")
            while True:
                if wait_for_connection(timeout_s=5):
                    if is_trigger_pressed():
                        handle_trigger()
                    else:
                        led_off()
                else:
                    led_off()
                    print("Lost connection, advertising...")
                    keyboard.start_advertising()
                sleep(0.05)
        else:
            if wait_for_trigger(timeout_s=10):
                handle_trigger()
            go_to_sleep()

    except Exception as e:
        print("Error:", e)
        led_off()
        if SLEEP_TIME_MS > 0:
            deepsleep(60 * 1000)


# -------------------------
# RUN MAIN
# -------------------------
main()
