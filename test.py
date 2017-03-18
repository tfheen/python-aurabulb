#! /usr/bin/python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
import logging
import binascii
import datetime

import aurabulb
from aurabulb import AuraBulb

logging.basicConfig(level=logging.DEBUG)

bd_addr = '11:75:58:dc:a7:08'
a = AuraBulb(bd_addr)

#print a.get_light_level()
#a.set_light_level(0xd0)
#a.set_light_level(200)
#print a.toggle_light()
#print a.get_light_color()
#print a.set_light_color(255, 00, 0)
#print a.set_light_mode(0)
#print a.get_voltage()
#print a.set_time(datetime.datetime.now())
print a.set_alarm_time(datetime.time(22, 04), 0, True)
print a.get_alarm_time()
