#!/usr/bin/env python
# -*- coding: utf-8 -*-
import smbus
import time
# BMP180 default
DEVICE            = 0x77
# Register
REG_CHIPID       = 0xD0
REG_RESET        = 0xE0
REG_CTRL_MEAS    = 0xF4
# Resolutions
RES_1            = 0x00
RES_2            = 0x01
RES_4            = 0x02
RES_8            = 0x03
# Classe
class bmp180:
  def __init__(self, i2cbus=0, device_address=DEVICE, res=RES_1):
    self.bus = smbus.SMBus(i2cbus)
    self.adr = device_address
    # Resolution
    if res not in [RES_1, RES_2, RES_4, RES_8]:
      raise ValueError('Unexpectedres value {0}.'.format(res))
    self.res = res
    # Load Calibration
    self._load_calibration()

  def get_chip_id(self):
    chip_id = self.bus.read_byte_data(self.adr, REG_CHIPID)
    return hex(chip_id)

  def reset(self):
    self.bus.write_byte_data(self.adr, REG_RESET, 0xB6)

  def is_measuring(self):
    return (self.bus.read_byte_data(self.adr, REG_CTRL_MEAS) & 0x05) != 0x00

  def get_resolution(self):
    return self.res

  def set_resolution(self, res):
    self.res = res

  def get_temperature(self):
    UT = self._get_temp_raw()
    # Calculate true Temperature
    X1 = ((UT - self.AC6) * self.AC5) >> 15
    X2 = (self.MC << 11) / (X1 + self.MD)
    B5 = X1 + X2
    t = ((B5 + 8) >> 4) / 10.0
    return t

  def get_pressure(self):
    UT = self._get_temp_raw()
    UP = self._get_press_raw()
    # Calculate true Pressure
    X1 = ((UT - self.AC6) * self.AC5) >> 15
    X2 = (self.MC << 11) / (X1 + self.MD)
    B5 = X1 + X2

    # Get B3
    B6 = B5 - 4000
    X1 = (self.B2 * (B6 * B6) >> 12) >> 11
    X2 = (self.AC2 * B6) >> 11
    X3 = X1 + X2
    B3 = (((self.AC1 * 4 + X3) << self.res) + 2) / 4
    # Get B4 and B7
    X1 = (self.AC3 * B6) >> 13
    X2 = (self.B1 * ((B6 * B6) >> 12)) >> 16
    X3 = ((X1 + X2) + 2) >> 2
    B4 = (self.AC4 * (X3 + 32768)) >> 15
    B7 = (UP - B3) * (50000 >> self.res)
    if B7 < 0x80000000:
      p = (B7 * 2) / B4
    else:
      p = (B7 / B4) * 2
    # Final
    X1 = (p >> 8) * (p >> 8)
    X1 = (X1 * 3038) >> 16
    X2 = (-7357 * p) >> 16
    p = p + ((X1 + X2 + 3791) >> 4)
    return p

  def get_temp_f(self):
    temp_c = self.get_temperature()
    temp_f = (temp_c * 1.8) + 32
    return temp_f

  def get_press_mmhg(self):
    press_pa = self.get_pressure()
    press_mm = press_pa * 0.0075
    return press_mm

  def get_altitude(self, pa_sealevel=101325.0):
    press = float(self.get_pressure())
    altitude  = 44330.0 * (1.0 - pow(press / pa_sealevel, (1.0/5.255)))
    return altitude

  def get_altitude_ft(self, pa_sealevel=101325.0):
    alti = self.get_altitude(pa_sealevel)
    alti_ft = alti / 0.3048
    return alti_ft

  def get_pasealevel(self, alti=0.0):
    press = float(self.get_pressure())
    pasea = press / pow(1.0 - alti/44330.0, 5.255)
    return pasea

  def get_pasealevel_mmhg(self, alti=0.0):
    pasea = self.get_pasealevel(alti)
    pasea_mm = pasea * 0.0075
    return pasea_mm

  def _get_temp_raw(self):
    self.bus.write_byte_data(self.adr, REG_CTRL_MEAS, 0x2E)
    # Wait for ready
    time.sleep(0.005)
    # Ready to read
    data = self.bus.read_i2c_block_data(self.adr, 0xF6, 2)
    UT = (data[0] << 8) + data[1]
    return UT

  def _get_press_raw(self):
    self.bus.write_byte_data(self.adr, REG_CTRL_MEAS, 0x34 + (self.res << 6))
    # Wait for ready
    if self.res == RES_1:
      time.sleep(0.005)
    elif self.res == RES_4:
      time.sleep(0.014)
    elif self.res == RES_8:
      time.sleep(0.026)
    else:
      time.sleep(0.008)
    # Ready to read
    data = self.bus.read_i2c_block_data(self.adr, 0xF6, 3)
    UP = ((data[0] << 16) + (data[1] << 8) + data[2]) >> (8 - self.res)
    return UP

  def _reads16(self, reg):
    result = self._readu16(reg)
    if result > 32767 :
      result -= 65536
    return result

  def _readu16(self, reg):
    MSB = self.bus.read_byte_data(self.adr, reg)
    LSB = self.bus.read_byte_data(self.adr, reg+1)
    return (MSB << 8) + LSB

  # Calibration
  def _load_calibration(self):
    # read all calibration registers
    self.AC1 = self._reads16(0xAA)
    self.AC2 = self._reads16(0xAC)
    self.AC3 = self._reads16(0xAE)
    self.AC4 = self._readu16(0xB0)
    self.AC5 = self._readu16(0xB2)
    self.AC6 = self._readu16(0xB4)
    self.B1 = self._reads16(0xB6)
    self.B2 = self._reads16(0xB8)
    self.MB = self._reads16(0xBA)
    self.MC = self._reads16(0xBC)
    self.MD = self._reads16(0xBE)
