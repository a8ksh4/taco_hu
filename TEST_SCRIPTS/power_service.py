#!/usr/bin/env python3

'''This script runs as a service and is responsible for the following:
  * Set display brightness on startup
  * Set display brightness every 15 minutes based on time of day
  * Monitor car acc line and:
      * if car is off, ensure display is off and amp is off.
      * If car is on, ensure display is on and amp is on.
  * Possibly monitor sound state to switch off amp when no auido playing.
  * TBD, probably follow some rules for pi shutdown after period of idle
    with car off, and setting wakeup timers so it's ready for probable 
    activity.  Wake at 7am, 4pm, shutdown after 1hr idle.
  * Check spicific gpio buttons and adjust brightness level based on userr
    input.
  * Potentially use astral package to compute daily dusk/dawn times for
    brightness curves.'''

import gpiod
import logging
import signal
import sys
import time
from datetime import datetime as dt


ACC_PIN = 4
AMP_PIN = 11
DISP_PW = '/sys/class/backlight/11-0045/bl_power'
DISP_BR = '/sys/class/backlight/11-0045/brightness'

# No need to change this for Pi 5:
CHIP = gpiod.Chip('gpiochip4')
AMP_LINE = None
ACC_LINE = None

MY_DIR = '/home/dan/git/taco_hu'
LOG_FILE = f'{MY_DIR}/taco_hu.log'
MUTEX_FILE = f'{MY_DIR}/mutex'

SIGINT_CAUGHT = False
def sigint_handler(signal, frame):
    global SIGINT_CAUGHT
    LOG.warning("Caught Ctrl C")
    SIGINT_CAUGHT = True



def get_logger():
    '''Get a logger that writes to a file and stdout.'''
    logger = logging.getLogger('simple_scheduler')
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


def get_sunrise_sunset_times():
    today = dt.today()
    isocal = today.isocalendar()
    day_num = isocal.week * 7 + isocal.weekday
    return (7, 16.45)


def set_brightness(value):
    '''value can be from 1 to 31.  0 is off, but
    we use bl_power for that.'''
    assert(value<32 and value>=0)
    with open(DISP_BR, 'w', encoding='utf-8') as f:
        f.write(value)


def set_backlight(state):
    '''Turns the touchscreen backlight on or off.  State can
    be one of "on" or "off". These are mapped to 0, on, or 1, off,
    and written to the bl_power device.'''
    assert(state in ('on', 'off'))
    value = '1' if state == 'off' else '0'
    with open(DISP_PW, 'w', encoding='utf-8') as f:
        f.write(value)


def set_amp_state(line, state):
    '''Turns the amp on/off.  State can be one of "on" or "off".'''
    assert(state in ('on', 'off'))
    value = 1 if state == 'off' else 0
    line.set_value(value)


def get_acc_state(line):
    '''Returns 'on' or 'off' based on hte acc pin.'''
    value = line.get_value()
    state = 'on' if value else 'off'
    return state


def main():
    '''main func...'''
    LOG.info('Initializing GPIO...')
    amp_line = CHIP.get_line(AMP_PIN)
    amp_line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)
    acc_line = CHIP.get_line(ACC_PIN)
    acc_line.request(consumer="Button", type=gpiod.LINE_REQ_DIR_IN)
    LOG.info('GPIO Ready, starting main loop...')
    
    acc_last = 'unknown'
    while True:
        if SIGINT_CAUGHT:
            break
        time.sleep(5)
        acc_state = get_acc_state(acc_line)
        if acc_state != acc_last:
            LOG.info(f'New ACC state: {acc_state}')
            acc_last = acc_state
        set_amp_state(amp_line, acc_state)
        set_backlight(acc_state)

    amp_line.release()
    acc_line.release()
    LOG.info('Pins reileased.  Main Func done.')


if __name__ == '__main__':
    LOG = get_logger()
    signal.signal(signal.SIGINT, sigint_handler)

    try:
        main()
    except Exception as e:
        LOG.error('Crash in main:')
        LOG.exception(e)

