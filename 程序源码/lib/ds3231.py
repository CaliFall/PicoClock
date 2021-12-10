#!/usr/bin/python
# -*- coding: utf-8 -*-
from machine import I2C
from machine import Pin
import time


address = 0x68
register = 0x00

#sec min hour week day mout year
NowTime = b'\x00\x00\x15\x04\x21\x01\x21'
w  = ["SUN","Mon","Tues","Wed","Thur","Fri","Sat"];

sda=Pin(14)
scl=Pin(15)

bus=I2C(1, scl=scl, sda=sda, freq=400000)


def SetTime():
	bus.writeto_mem(int(address),int(register),NowTime)

def ReadTime():
	return bus.readfrom_mem(int(address),int(register),7);

def FormatTime():
        t = ReadTime()
        a = t[0]&0x7F  #sec
        b = t[1]&0x7F  #min
        c = t[2]&0x3F  #hour
        d = t[3]&0x07  #week
        e = t[4]&0x3F  #day
        f = t[5]&0x1F  #mouth
        # return("20%x/%02x/%02x %02x:%02x:%02x %s" %(t[6],t[5],t[4],t[2],t[1],t[0],w[t[3]-1]))
        return t

def ReportDate():
    t = FormatTime()
    return("20%x/%02x/%02x" % (t[6],t[5],t[4]))

def ReportWeek():
    t = FormatTime()
    return("%s" % (w[t[3]-1]))
    
def ReportTime():
    t = FormatTime()
    return("%02x:%02x:%02x" % (t[2],t[1],t[0]))


        
if __name__ == '__main__':
    #SetTime()
    while 1:
        print(ReportTime())
        time.sleep(1)
