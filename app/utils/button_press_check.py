#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Developer: Nigel Bowden
    
    button_press_check.py - Check button pin numbers on GPIO

    Usage: python3 button_press_check.py

    When the script is run, it will loop and reports any button presses detected on the GPIO pins (pins 2 to 28).
    These can be used to map functions in FPMS

"""
from gpiozero import Button
import time

buttons_dict = {}

for button in range(2, 28):
    buttons_dict[str(button)] = Button(button) 

while True:
    for button_number, button_obj in buttons_dict.items():
        if button_obj.is_pressed:
            print("Button is pressed: " + str(button_number))

    time.sleep(0.1)