from machine import Pin, Timer
import time
from ssd1306 import SSD1306_I2C
import random

led_g = Pin(14,Pin.OUT)
led_r = Pin(15,Pin.OUT)

tim = Timer()

def tick_g(timer):
    global led_g
    led_g.toggle()
    
def tick_r(timer):
    global led_r
    led_r.toggle()
    
# tim.init(period=500, mode=Timer.PERIODIC,callback=tick_r)
tim.deinit

sda=machine.Pin(16)
scl=machine.Pin(17)
 
i2c=machine.I2C(0, sda=sda, scl=scl, freq=400000)
print(i2c.scan())
oled = SSD1306_I2C(128, 64, i2c)

def ezline(msg):
    oled.scroll(0,-9)
    oled.text(msg,0,-5)
    oled.show()
    time.sleep_ms(1000)

if __name__ == "__main__":

    msg = "HelloWorld | HelloWorld | HelloWorld | Helloworld | Helloworld | "
    
    while True:
        a=1
        for x in range(-128,128+1,):
            for y in range(-128,128+1,8):
                oled.text(msg,x,y+a)
                
            oled.show()
            oled.fill(0)
            a+=1

        