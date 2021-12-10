# Example using PWM to fade an LED.

import utime
from machine import Pin, PWM

# Construct PWM object, with LED on Pin(25).
pwm_r = PWM(Pin(0))
pwm_g = PWM(Pin(1))
pwm_led = PWM(Pin(25))

# Set the PWM frequency.
pwm_r.freq(1000)
pwm_g.freq(1000)
pwm_led.freq(1000)

# Fade the LED in and out a few times.
duty = 0
direction = 1
while True:
    duty += direction
    if duty > 255:
        duty = 255
        direction = -1
    elif duty < 0:
        duty = 0
        direction = 1
    pwm_r.duty_u16(duty * duty)
    pwm_g.duty_u16(int((65536 - duty * duty)/2))
    pwm_led.duty_u16(duty ** 2)
    utime.sleep_ms(10)