#!/usr/bin/env python3
'''
This is the monolithic thing that checks gpio buttons, monitors acc line
* sets the display brigntness
* turns amp on/off with acc line
* sends hudiy actions for play/pause, volume up/down etc...
* Turns the screen off when the car's acc line is off
* Shuts the system down a while after the car is turned off
* Sets wake timers so the system will wake up at certain times
  (like before morning commute, and before evening commute)
  to be ready to go when you get in the car.

Gpio button magic functionality that is intended to be implemented here:
* Tap to perform operation
* Long press/hold to perform operation or repeated operation (keep turning volume down)
* Double tap to perform alternate operation (next track)
* Chord/combo press to peform a different operation!
'''

import common.Api_pb2 as hudiy_api
from common.Client import Client, ClientEventHandler
# import serial
# import subprocess
import fcntl
import logging
import os
import threading
# from collections import deque
import time
from gpiozero import Button, OutputDevice, InputDevice
from signal import pause
import subprocess as sp


# This is the path I have for the official touchscreen two on pi os trixie.  
# You may need to change it for your system.
BL_PATH = '/sys/class/backlight/11-0045'

ACC_PIN = 4  # GPIO pin connected to optocopuple for car ACC line
ACC = InputDevice(ACC_PIN, pull_up=True)  # , bounce_time=0.05)  # pulled high, goes low when ACC on
AMP_PIN = 11  # GPIO connected to relay to switch amp on/off
AMP = OutputDevice(AMP_PIN, active_high=True, initial_value=False)

BUTTON_PRESSED = False  # Tracker that lets us activate display for period of time on button press
BUTTON_TIMEOUT = 60*5  # five minutes

SHUTDOWN_TIMEOUT = 60*15 # 15 minutes after acc off to shutdown system

WAKE_TIMES = [  # (hour, minute) tuples for rtc wake alarms
    '7:30',  # Morning commute
    '11:00',  # Lunch
    '16:00',  # Evening commute
]

# GPIO Pins that have buttons connected
# Buttons should connect to ground and a gpio.  
# They're pulled high and pressed when connected to ground.
BUTTONS_PINS = [6, 19, 13, 20, 21, 16, 26]
BUTTONS = [Button(p, pull_up=True, bounce_time=0.05) for p in BUTTONS_PINS]
# These are just helper names for logging so you can figure stuff out
NAMES = ['play', 'esc', 'mute', 'br_up', 'br_dn', 'vl_up', 'vl_dn']
# Add checks in the get_press_func for your custom operations here. 
# These map to the button pins and names above.
HU_ACTIONS = ['now_playing_toggle_play',
              'equalizer_preset_settings',
              'resume_android_auto_projection',  # 'go_back',
              'display_brightness_up',
              'display_brightness_down',
              'output_volume_up',
              'output_volume_down']

MY_DIR = '/home/dan/git/taco_hu'
LOG_FILE = f'{MY_DIR}/taco_truck.log'
MUTEX_FILE = f'{MY_DIR}/taco_truck.mutex'

# For clean exit when we kill the service
SIGINT_CAUGHT = False
def sigint_handler(signal, frame):
    global SIGINT_CAUGHT
    LOG.warning("Caught Ctrl C or something!")
    SIGINT_CAUGHT = True


def get_logger():
    '''Get a logger that writes to a file and stdout.'''
    logger = logging.getLogger('taco_truck')
    logger.setLevel(logging.DEBUG)
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format_str)
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def get_press_func(pin, name, client, actionstr):
    '''Generate on_press function for button'''
    if actionstr == 'display_brightness_up':
        def on_press():
            global BUTTON_PRESSED
            BUTTON_PRESSED = True
            LOG.info(f"pressed: {pin}, {name}, {actionstr}")
            change_brightness(up=True)
    elif actionstr == 'display_brightness_down':
        def on_press():
            global BUTTON_PRESSED
            BUTTON_PRESSED = True
            LOG.info(f"pressed: {pin}, {name}, {actionstr}")
            change_brightness(up=False)
    else:
        def on_press():
            global BUTTON_PRESSED
            BUTTON_PRESSED = True
            LOG.info(f"pressed: {pin}, {name}, {actionstr}")
            trigger_action(client, actionstr)

    return on_press

def set_next_rtc_wake_timer():
    '''set rtc wake alarm for next wake time'''




def display_power(on=True):
    '''Turns the lcd display on or off'''
    # /sys/class/backlight/11-0045/bl_power
    power_file = f'{BL_PATH}/bl_power'
    with open(power_file, 'w', encoding='utf-8') as pf:
        if on:
            pf.write('0')  # 0 is on
            LOG.info("Display powered ON")
        else:
            pf.write('4')  # 4 is off
            LOG.info("Display powered OFF")



def change_brightness(up=True):
    '''Does not use hudiy.  Change the system brigntness directly'''
    max_file = f'{BL_PATH}/max_brightness'
    with open(max_file, 'r', encoding='utf-8') as mf:
        max_brightness = int(mf.read().strip())
    set_file = f'{BL_PATH}/brightness'
    with open(set_file, 'r', encoding='utf-8') as sf:
        cur_brightness = int(sf.read().strip())
    step = 3

    if up:
        new_brightness = min(max_brightness, cur_brightness + step)
    else:
        new_brightness = max(0, cur_brightness - step)
    with open(set_file, 'w', encoding='utf-8') as sf:
        sf.write(str(new_brightness))
    LOG.info(f"Brightness changed from {cur_brightness} to {new_brightness}")


class EventHandler(ClientEventHandler):
    '''Event handler for events generated by hudiy'''
    def on_hello_response(self, client, message):
        LOG.debug(
            "received hello response, result: {}, app version: {}.{}, api version: {}.{}"
            .format(message.result, message.app_version.major,
                    message.app_version.minor, message.api_version.major,
                    message.api_version.minor))

        set_status_subscriptions = hudiy_api.SetStatusSubscriptions()
        set_status_subscriptions.subscriptions.append(
                hudiy_api.SetStatusSubscriptions.Subscription.MEDIA)
        client.send(hudiy_api.MESSAGE_SET_STATUS_SUBSCRIPTIONS,
                0, set_status_subscriptions.SerializeToString())


def trigger_action(client, actionstr):
    '''Trigger action like next song, volume up etc...'''
    try:
        dispatch_action = hudiy_api.DispatchAction()
        dispatch_action.action = actionstr
        client.send(hudiy_api.MESSAGE_DISPATCH_ACTION,
                    0, dispatch_action.SerializeToString())
    except Exception as e:
        LOG.exception(f"Failed to trigger action {actionstr}: {e}")


def hudiy_listener(client):
    '''Must be here, otherwise connection is broken after few moments'''
    LOG.info("HUDIY listener started")
    while True:
        try:
            client.wait_for_message()
        except Exception as e:
            LOG.exception(f"HUDIY listener failed: {e}")
            break


def main():
    '''Main function'''
    global BUTTON_PRESSED

    # Wait for hudiy to start
    while True:
        try:
            sp.check_call(['pgrep', '-f', 'hudiy'])
            break
        except sp.CalledProcessError:
            LOG.info("Waiting for hudiy to start...")
            time.sleep(5)
    LOG.info("hudiy is running, continuing...")
    time.sleep(10)  # wait a bit more for hudiy to be ready

    # Connection to hudiy
    client = Client("HUDIY Discovery II")
    event_handler = EventHandler()
    client.set_event_handler(event_handler)
    client.connect('127.0.0.1', 44406, use_websocket=True)

    threading.Thread(target=hudiy_listener, args=(client,), daemon=True).start()

    for pin, butt, name, action in zip(BUTTONS_PINS, BUTTONS, NAMES, HU_ACTIONS):
        LOG.info(f"Setting up button on pin {pin} for {name} action {action}")
        butt.when_pressed = get_press_func(pin, name, client, action)

    print("Main loop starting...")
    button_timer = time.time() # in seconds
    acc_last_state = ACC.is_active
    acc_timer = time.time()  # in seconds
    while True:
        # Button presses happen in the background
        if BUTTON_PRESSED:
            LOG.info("Button pressed, setting button timer")
            button_timer = time.time()
            BUTTON_PRESSED = False

        # Button timers reset on acc change so turning car off takes effect immediately
        if ACC.is_active != acc_last_state:
            LOG.info("ACC state changed, clearing button timer")
            button_timer = 0  # reset timer on acc change
            acc_timer = time.time()
        acc_last_state = ACC.is_active

        # Check button timeout to turn stuff on if 
        if time.time() - button_timer < BUTTON_TIMEOUT:
            if not AMP.value:
                LOG.info("Turning on based on button activity")
                display_power(on=True)
                AMP.on()
        
        # Check shutdown timeout
        elif ( not ACC.is_active and not AMP.value
                and (time.time() - acc_timer) > SHUTDOWN_TIMEOUT
                and (time.time() - button_timer) > SHUTDOWN_TIMEOUT ):
            LOG.info("ACC off for too long, shutting down system")
            client.disconnect()
            # LOG.debug(f"Buttom_timer: {button_timer}, acc_timer: {acc_timer}, now: {time.time()}")
            sp.Popen(['sudo', 'shutdown', '-h', 'now'])
            time.sleep(10)
            break

        # Check ACC status and do stuff!
        elif not ACC.is_active:
            if AMP.value:
                LOG.info("ACC off, turning amp off")
                AMP.off()

                # Send audio stop action to hudiy
                trigger_action(client, 'now_playing_stop')

                display_power(on=False)
    
        else:  # Truck is on
            if not AMP.value:
                LOG.info("ACC on, turning amp on")
                AMP.on()
                display_power(on=True)

        # Sigint stuff for clean exit
        if SIGINT_CAUGHT:
            break

        # pause()  # presum sigint caught will break this
        time.sleep(1)

    client.disconnect()


if __name__ == "__main__":
    LOG = get_logger()

    # Get mutex to prevent multiple instances
    with open(MUTEX_FILE, 'w') as mf:
        try:
            fcntl.flock(mf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            LOG.error("Another instance is running, exiting")
            exit(1)

    # # Check if uinput module is loaded or load it
    # if not os.path.exists('/dev/uinput'):
    #     sp.check_call(['sudo', 'modprobe', 'uinput'])

    # # Change the acct name here if you use this under different user
    #     sp.check_call(['sudo', 'chown', 'dan', '/dev/uinput'])

    LOG.info("Starting buttons service")
    try:
        main()
    except Exception as e:
        LOG.exception(f"Exception in main: {e}")
    LOG.info("Exiting buttons service")
    
