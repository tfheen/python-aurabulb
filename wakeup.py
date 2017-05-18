#! /usr/bin/python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
import logging
import binascii
import time
import datetime
import sched

import aurabulb
from aurabulb import AuraBulb
from aurabulb import constants as aura_constants

logging.basicConfig(level=logging.INFO)

bd_addr = '11:75:58:dc:a7:08'
a = AuraBulb(bd_addr)

class WakeupLight(object):
    def __init__(self, aurabulb, start, end, color = (255, 255, 255)):
        self.start = start
        self.end = end
        self.aurabulb = aurabulb
        self.aurabulb.set_light_level(0)

    def start_wakeup(self, scheduler):
        stepsize = (self.end-self.start)/aura_constants.MAX_LIGHT_LEVEL
        steps = [x*stepsize for x in range(aura_constants.MAX_LIGHT_LEVEL+1)]
        logging.info("Steps are: %s", steps)
        for s in steps:
            scheduler.enter(s, 1, self.set_level_from_time, ())

    def set_level_from_time(self):
        total_len = self.end - self.start
        elapsed = time.time() - self.start
        level = int(aura_constants.MAX_LIGHT_LEVEL * (elapsed/total_len))
        logging.info("Setting level to: %d", level)
        self.aurabulb.set_light_level(level)

    def run(self):
        if time.time() > self.end:
            return
        s = sched.scheduler(time.time, time.sleep)
        s.enterabs(self.start, 1, self.start_wakeup, (s,))
        s.run()

start_day = datetime.date.today()
start_time = datetime.time(8,00)
end_day = datetime.date.today()
end_time = datetime.time(8,30)
start = time.mktime(datetime.datetime.combine(start_day, start_time).timetuple())
end = time.mktime(datetime.datetime.combine(end_day, end_time).timetuple())

l = WakeupLight(a, start, end)
l.run()
