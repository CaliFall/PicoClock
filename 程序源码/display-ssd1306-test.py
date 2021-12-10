import machine
from utime import sleep,sleep_ms
from ssd1306 import SSD1306_I2C
import ds3231
 
sda1=machine.Pin(0)
scl1=machine.Pin(1)
sda2=machine.Pin(14)
scl2=machine.Pin(15)
 
i2c1=machine.I2C(0, sda=sda1, scl=scl1, freq=400000)
i2c2=machine.I2C(1, sda=sda2, scl=scl2, freq=400000)

print(i2c1.scan())
print(i2c2.scan())


oled1 = SSD1306_I2C(128, 64, i2c1)
oled2 = SSD1306_I2C(128, 32, i2c2)

while True:
    oled1.fill(0)
    
    oled1.text(ds3231.ReportDate(),0,0*8)
    oled1.text(ds3231.ReportTime(),0,1*8)
    oled1.text(ds3231.ReportWeek(),0,2*8)
    
    oled1.show()
    sleep_ms(250)
    

    

