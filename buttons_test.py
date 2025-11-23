#!/usr/bin/env python3

import uinput
from gpiozero import Button
from signal import pause

BUTTONS_PINS = [16, 26, 21, 20, 19, 13, 6]
BUTTONS = [Button(p, pull_up=True, bounce_time=0.05) for p in BUTTONS_PINS]
NAMES = ['vl_up', 'vl_dn', 'br_dn', 'br_up', 'mute', 'esc', 'play']
KEYS = [uinput.KEY_VOLUMEUP,
        uinput.KEY_VOLUMEDOWN,
        uinput.KEY_BRIGHTNESSDOWN,
        uinput.KEY_BRIGHTNESSUP,
        uinput.KEY_MUTE,
        uinput.KEY_H,  # uinput.KEY_ESC,
        uinput.KEY_B]  # uinput.KEY_PLAYPAUSE]
DEVICE = uinput.Device(KEYS)

def get_press_func(pin, name, key):
    def on_press():
        print("pressed:", pin, name)
        DEVICE.emit(key, 1)

    return on_press


def get_release_func(pin, name, key):
    def on_release():
        print("released:", pin, name)
        DEVICE.emit(key, 0)

    return on_release


for PIN, BUTT, NAME, KEY in zip(BUTTONS_PINS, BUTTONS, NAMES, KEYS):
    BUTT.when_pressed = get_press_func(PIN, NAME, KEY)
    BUTT.when_released = get_release_func(PIN, NAME, KEY)

print("Waiting for buton presses...")
pause()

