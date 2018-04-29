#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bmp180

if __name__ == '__main__':
  bmp = bmp180.bmp180()
  # Read Data
  tc = bmp.get_temperature()
  tf = bmp.get_temp_f()
  pp = bmp.get_pressure()
  ph = bmp.get_press_mmhg()
  am = bmp.get_altitude()
  af = bmp.get_altitude_ft()
  sp = bmp.get_pasealevel()
  sh = bmp.get_pasealevel_mmhg()
  chipid = bmp.get_chip_id()

  print "Temperature: %.2f C" % tc
  print "Temperature: %.2f F" % tf
  print "Pressure: %.2f hPa" % (pp/100)
  print "Pressure: %.2f mmHg" % ph
  print "Altitude: %.2f m" % am
  print "Altitude: %.2f ft" % af
  print "SeaLevel Pressure: %.2f hPa" % (sp/100)
  print "SeaLevel Pressure: %.2f mmHg" % sh
  print "Chip ID: {0}".format(chipid)
