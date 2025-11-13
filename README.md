# taco_hu
Customization and setup tools for hudiy in my taco.


# Fixing idle power use
    https://www.jeffgeerling.com/blog/2023/reducing-raspberry-pi-5s-power-consumption-140x
    Edit your EEPROM config by running sudo rpi-eeprom-config -e, and make
    sure the following settings are configured:
    
    [all]
    BOOT_UART=1
    WAKE_ON_GPIO=0
    POWER_OFF_ON_HALT=1

# Testing Display Brightness and Backlight shutdown.
    In order to turn the backlight off when the pi is shut
    down, you need to switch it off during shutdown sequence.
    See the setup_touchscreen_power_controls.sh script.

    dan@taco:~ $ echo 1 | sudo tee /sys/class/backlight/11-0045/bl_power
    1  # Displai power off
    dan@taco:~ $ echo 0 | sudo tee /sys/class/backlight/11-0045/bl_power
    0  # Display power on

    And brightness is controlled similarly:

    dan@taco:~ $ ll /sys/class/backlight/11-0045/
    actual_brightness  device/            power/             type
    bl_power           display_name       scale              uevent
    brightness         max_brightness     subsystem/         
    dan@taco:~ $ cat /sys/class/backlight/11-0045/brightness 
    31
    dan@taco:~ $ cat /sys/class/backlight/11-0045/max_brightness 
    31
    dan@taco:~ $ cat /sys/class/backlight/11-0045/display_name 
    DSI-2
    dan@taco:~ $ echo 5 > /sys/class/backlight/11-0045/brightness
        # Kinda dim
    dan@taco:~ $ echo 1 > /sys/class/backlight/11-0045/brightness
        # Dim
    dan@taco:~ $ echo 0 > /sys/class/backlight/11-0045/brightness
        # Off
    dan@taco:~ $ echo 1 > /sys/class/backlight/11-0045/brightness
    dan@taco:~ $ echo 31 > /sys/class/backlight/11-0045/brightness
        # Bright

# Testing the acc line read
    dan@taco:~ $ python3
    Python 3.11.2 (main, Apr 28 2025, 14:11:48) [GCC 12.2.0] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import gpiod
    >>> chip = gpiod.Chip('gpiochip4')
    >>> acc_pin = 4
    >>> acc_line = chip.get_line(acc_pin)
    >>> acc_line.request(consumer="Button", type=gpiod.LINE_REQ_DIR_IN)
    >>> print(acc_line.get_value())
    1
    >>> print(acc_line.get_value())
    0

# Testing the amp line relay toggle
    dan@taco:~ $ python3
    Python 3.11.2 (main, Apr 28 2025, 14:11:48) [GCC 12.2.0] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import gpiod
    >>> chip = gpiod.Chip('gpiochip4')
    >>> amp_pin = 11
    >>> amp_line = chip.get_line(amp_pin)
    >>> amp_line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)
    >>> amp_line.set_value(1)
    >>> amp_line.set_value(0)
    >>> 
    
