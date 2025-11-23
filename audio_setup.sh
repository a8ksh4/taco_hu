#!/bin/sh

#SUB="alsa_output.usb-Apple__Inc._USB-C_to_3.5mm_Headphone_Jack_Adapter_DWH52430BA92FN3AJ-00.analog-stereo"
#DOORS="alsa_output.usb-Apple__Inc._USB-C_to_3.5mm_Headphone_Jack_Adapter_DWH52440FGT2FN3AB-00.analog-stereo"

# Combine Sinks:
#if ! pactl list short sinks | grep taco_sound; then
#pactl load-module module-combine-sink \
#    slaves=$DOORS,$SUB \
#    channels=3 \
#    sink_name="taco_sound" 
#    #channel_map="front_Left,front_right" #,subwoofer"
#    echo "Created combined sink!"
#else
#    echo "Combined sink reported by pactl!"
#fi
#
pactl set-default-sink taco_sound
#pactl set-default-sink combined

mkdir -p ~/.config/pipewire/filter-chain.conf.d
cp ./taco-dsp.conf  ~/.config/pipewire/filter-chain.conf.d/

mkdir -p ~/.config/pipewire/pipewire.conf.d
cp ./taco_combine.conf ~/.config/pipewire/pipewire.conf.d/
