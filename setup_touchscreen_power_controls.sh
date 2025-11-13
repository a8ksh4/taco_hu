#!/bin/sh

PW='/sys/class/backlight/*/bl_power'

echo "Press <enter> to test toggle touchscreen power.  It shuld turn off and back on again."
read FOO

echo 1 | sudo tee $PW
sleep 1
echo 0 | sudo tee $PW

SD_SCRIPT="/lib/systemd/system-shutdown/99-backlight-off"

if ! test -f $SD_SCRIPT; then
    echo "Shutdown script not present."
    echo "Press <enter> to create $SD_SCRIPT"
    echo "Or <ctrl> + <c> to quit."
    read FOO

    sudo tee $SD_SCRIPT <<'EOF'
#!/bin/sh
# systemd calls this with "halt", "poweroff", "reboot" or "kexec"
for d in /sys/class/backlight/*; do
  [ -e "$d/bl_power" ] && echo 1 > "$d/bl_power" 2>/dev/null
  [ -e "$d/brightness" ] && echo 0 > "$d/brightness" 2>/dev/null
done
exit 0
EOF
    sudo chmod +x $SD_SCRIPT
fi

# Udev rule for setting video group on backlight controls.
# This is so we don't need to run our service with root...
UDEV_FILE='/etc/udev/rules.d/90-backlight-uaccess.rules'
if ! test -f $UDEV_FILE; then
    echo 'SUBSYSTEM=="backlight", ACTION=="add|change", KERNEL=="*", \
    RUN+="/bin/chgrp -R video /sys/class/backlight/%k/", \
    RUN+="/bin/chmod g+w /sys/class/backlight/%k/brightness", \
    RUN+="/bin/chmod g+w /sys/class/backlight/%k/bl_power"
    ' | sudo tee $UDEV_FILE

    sudo udevadm control --reload
    sudo udevadm trigger -s backlight
fi

