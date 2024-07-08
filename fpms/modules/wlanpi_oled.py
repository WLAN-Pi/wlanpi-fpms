#!/usr/bin/env python
# -*- coding: utf-8 -*-

import spidev
import time
import numpy as np

from gpiozero import *
from fpms.modules.constants import PLATFORM
from fpms.modules.platform import *

LCD_WIDTH, LCD_HEIGHT, LCD_X, LCD_Y = 128, 128, 2, 1

LCD_X_MAXPIXEL = 132  # LCD width maximum memory
LCD_Y_MAXPIXEL = 162  # LCD height maximum memory

# scanning method
SCAN_DIR_DFT = 6  # U2D_R2L

class RaspberryPi:
    def __init__(self, spi=spidev.SpiDev(0, 0), spi_freq=40000000, rst=27, dc=25, bl=24, bl_freq=1000, i2c=None, i2c_freq=100000):
        self.np = np
        self.INPUT = False
        self.OUTPUT = True

        self.SPEED = spi_freq
        self.BL_freq = bl_freq

        self.GPIO_RST_PIN = self.gpio_mode(rst, self.OUTPUT)
        self.GPIO_DC_PIN = self.gpio_mode(dc, self.OUTPUT)
        self.GPIO_BL_PIN = self.gpio_pwm(bl)
        self.bl_DutyCycle(0)

        # Initialize SPI
        self.SPI = spi
        if self.SPI:
            self.SPI.max_speed_hz = spi_freq
            self.SPI.mode = 0b00

    def gpio_mode(self, Pin, Mode, pull_up=None, active_state=True):
        if Mode:
            return DigitalOutputDevice(Pin, active_high=True, initial_value=False)
        else:
            return DigitalInputDevice(Pin, pull_up=pull_up, active_state=active_state)

    def digital_write(self, Pin, value):
        if value:
            Pin.on()
        else:
            Pin.off()

    def digital_read(self, Pin):
        return Pin.value

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def gpio_pwm(self, Pin):
        return PWMOutputDevice(Pin, frequency=self.BL_freq)

    def spi_writebyte(self, data):
        if self.SPI:
            self.SPI.writebytes(data)

    def bl_DutyCycle(self, duty):
        self.GPIO_BL_PIN.value = duty / 100

    def bl_Frequency(self, freq):
        self.GPIO_BL_PIN.frequency = freq

    def module_init(self):
        if self.SPI:
            self.SPI.max_speed_hz = self.SPEED
            self.SPI.mode = 0b00
        return 0

    def module_exit(self):
        if self.SPI:
            self.SPI.close()

        self.digital_write(self.GPIO_RST_PIN, 1)
        self.digital_write(self.GPIO_DC_PIN, 0)
        self.GPIO_BL_PIN.close()
        time.sleep(0.001)

class LCD(RaspberryPi):
    width, height = LCD_WIDTH, LCD_HEIGHT
    LCD_Scan_Dir = SCAN_DIR_DFT
    LCD_X_Adjust, LCD_Y_Adjust = LCD_X, LCD_Y

    def LCD_Reset(self):
        self.digital_write(self.GPIO_RST_PIN, True)
        time.sleep(0.01)
        self.digital_write(self.GPIO_RST_PIN, False)
        time.sleep(0.01)
        self.digital_write(self.GPIO_RST_PIN, True)
        time.sleep(0.01)

    def LCD_WriteReg(self, Reg):
        self.digital_write(self.GPIO_DC_PIN, False)
        self.spi_writebyte([Reg])

    def LCD_WriteData_8bit(self, Data):
        self.digital_write(self.GPIO_DC_PIN, True)
        self.spi_writebyte([Data])

    def LCD_WriteData_NLen16Bit(self, Data, DataLen):
        self.digital_write(self.GPIO_DC_PIN, True)
        for _ in range(DataLen):
            self.spi_writebyte([Data >> 8, Data & 0xff])

    def LCD_InitReg(self):
        init_sequence = [
            (0xB1, [0x01, 0x2C, 0x2D]),
            (0xB2, [0x01, 0x2C, 0x2D]),
            (0xB3, [0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D]),
            (0xB4, [0x07]),
            (0xC0, [0xA2, 0x02, 0x84]),
            (0xC1, [0xC5]),
            (0xC2, [0x0A, 0x00]),
            (0xC3, [0x8A, 0x2A]),
            (0xC4, [0x8A, 0xEE]),
            (0xC5, [0x0E]),
            (0xe0, [0x0f, 0x1a, 0x0f, 0x18, 0x2f, 0x28, 0x20, 0x22, 0x1f, 0x1b, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10]),
            (0xe1, [0x0f, 0x1b, 0x0f, 0x17, 0x33, 0x2c, 0x29, 0x2e, 0x30, 0x30, 0x39, 0x3f, 0x00, 0x07, 0x03, 0x10]),
            (0xF0, [0x01]),
            (0xF6, [0x00]),
            (0x3A, [0x05])
        ]
        for reg, data in init_sequence:
            self.LCD_WriteReg(reg)
            for d in data:
                self.LCD_WriteData_8bit(d)

    def LCD_SetGramScanWay(self, Scan_dir):
        self.LCD_Scan_Dir = Scan_dir
        self.width, self.height = (LCD_HEIGHT, LCD_WIDTH) if Scan_dir in [1, 2, 3, 4] else (LCD_WIDTH, LCD_HEIGHT)
        MemoryAccessReg_Data = {
            1: 0x00, 2: 0x80, 3: 0x40, 4: 0xC0,
            5: 0x20, 6: 0x60, 7: 0xA0, 8: 0xE0
        }[Scan_dir]

        if MemoryAccessReg_Data & 0x10 != 1:
            self.LCD_X_Adjust, self.LCD_Y_Adjust = LCD_Y, LCD_X
        else:
            self.LCD_X_Adjust, self.LCD_Y_Adjust = LCD_X, LCD_Y

        self.LCD_WriteReg(0x36)
        self.LCD_WriteData_8bit(MemoryAccessReg_Data | 0x08)

    def LCD_Init(self, Lcd_ScanDir):
        if self.module_init() != 0:
            return -1
        self.bl_DutyCycle(100)
        self.LCD_Reset()
        self.LCD_InitReg()
        self.LCD_SetGramScanWay(Lcd_ScanDir)
        self.delay_ms(200)
        self.LCD_WriteReg(0x11)
        self.delay_ms(120)
        self.LCD_WriteReg(0x29)

    def LCD_SetWindows(self, Xstart, Ystart, Xend, Yend):
        self.LCD_WriteReg(0x2A)
        self.LCD_WriteData_8bit(0x00)
        self.LCD_WriteData_8bit((Xstart & 0xff) + self.LCD_X_Adjust)
        self.LCD_WriteData_8bit(0x00)
        self.LCD_WriteData_8bit(((Xend - 1) & 0xff) + self.LCD_X_Adjust)

        self.LCD_WriteReg(0x2B)
        self.LCD_WriteData_8bit(0x00)
        self.LCD_WriteData_8bit((Ystart & 0xff) + self.LCD_Y_Adjust)
        self.LCD_WriteData_8bit(0x00)
        self.LCD_WriteData_8bit(((Yend - 1) & 0xff) + self.LCD_Y_Adjust)

        self.LCD_WriteReg(0x2C)

    def LCD_Clear(self):
        _buffer = [0x00, 0x00] * (self.width * self.height)
        self.LCD_SetWindows(0, 0, self.width, self.height)
        self.digital_write(self.GPIO_DC_PIN, True)
        for i in range(0, len(_buffer), 4096):
            self.spi_writebyte(_buffer[i:i + 4096])

    def LCD_ShowImage(self, Image, Xstart, Ystart):
	    if Image is None:
	        return
	    imwidth, imheight = Image.size
	    if imwidth != self.width or imheight != self.height:
	        raise ValueError(f'Image must be same dimensions as display ({self.width}x{self.height}).')
	    img = np.asarray(Image)
	    pix = np.zeros((self.width, self.height, 2), dtype=np.uint8)
	    pix[..., 0] = np.add(np.bitwise_and(img[..., 0], 0xF8), np.right_shift(img[..., 1], 5))
	    pix[..., 1] = np.add(np.bitwise_and(np.left_shift(img[..., 1], 3), 0xE0), np.right_shift(img[..., 2], 3))
	    pix = pix.flatten().tolist()
	    self.LCD_SetWindows(0, 0, self.width, self.height)
	    self.digital_write(self.GPIO_DC_PIN, True)
	    for i in range(0, len(pix), 4096):
	        self.spi_writebyte(pix[i:i+4096])

    def LCD_Backlight(self, onOff):
        if onOff == True:
            self.bl_DutyCycle(100)
        else:
            self.bl_DutyCycle(0)

device = LCD()

# Init function of the OLED
def init():
    Lcd_ScanDir = SCAN_DIR_DFT  #SCAN_DIR_DFT = D2U_L2R
    device.LCD_Init(Lcd_ScanDir)
    device.LCD_Clear()
    return True

def setNormalDisplay():
    return True

def setHorizontalMode():
    return True

def drawImage(image):
    img = image
    width, height = image.size
    if LCD_WIDTH != width or LCD_HEIGHT != height:
        img = img.resize((LCD_WIDTH, LCD_HEIGHT), Image.LANCZOS)

    device.LCD_ShowImage(img, 0, 0)

def clear():
    device.LCD_Clear()

def sleep():
    device.LCD_Clear()
    device.LCD_Backlight(False)

def wakeup():
    device.LCD_Backlight(True)
