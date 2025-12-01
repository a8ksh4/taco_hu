#!/usr/bin/env python3

'''
This script/service checks configured gpio pins connected to buttons. 
The buttons short the pin to ground, so all pins need to be pulled high
and will read low when the buttons are pressed. 

Buttons correspond with keypresses using uinput.  
'''

import 
import logging
import signal
import sys
import time
from datetime import datetime as dt


BUTTONS_PINS = [26, 21, 20, 19, 13, 6, 5]
BUTTONS = [{'pin': p} for p in BUTTONS_PINS]

# No need to change this for Pi 5:
CHIP = gpiod.Chip('gpiochip0')

MY_DIR = '/home/dan/git/taco_hu'
LOG_FILE = f'{MY_DIR}/buttons.log'
MUTEX_FILE = f'{MY_DIR}/buttons.mutex'

SIGINT_CAUGHT = False
def sigint_handler(signal, frame):
    global SIGINT_CAUGHT
    LOG.warning("Caught Ctrl C")
    SIGINT_CAUGHT = True


def get_logger():
    '''Get a logger that writes to a file and stdout.'''
    logger = logging.getLogger('taco_buttons')
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


def get_acc_state(line):
    '''Returns 'on' or 'off' based on hte acc pin.'''
    value = line.get_value()
    state = 'on' if value else 'off'
    return state


def main():
    '''main func...'''
    LOG.info('Initializing GPIO...')
    for button in BUTTONS:
        button['line'] = CHIP.get_line(button['pin'])
        button['line'].reques(consumer="Button", type=gpiod.LINE_REQ_DIR_IN)
        LOG.info(f'Button {button["pin"]} ready!')

    LOG.info('GPIO Ready, starting main loop...')
    
    acc_last = 'unknown'
    while True:
        if SIGINT_CAUGHT:
            break
        time.sleep(5)
        for button in BUTTONS:
            print(f'Button {button["pin"]}: {button["line"].get_value()}')

    for button in BUTTONS:
        button['line'].release()
    LOG.info('Pins reileased.  Main Func done.')


if __name__ == '__main__':
    LOG = get_logger()
    signal.signal(signal.SIGINT, sigint_handler)

    try:
        main()
    except Exception as e:
        LOG.error('Crash in main:')
        LOG.exception(e)

