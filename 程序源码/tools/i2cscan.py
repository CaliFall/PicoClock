import machine

sda_0 = machine.Pin(0)
scl_0 = machine.Pin(1)
sda_1 = machine.Pin(14)
scl_1 = machine.Pin(15)

# 定义0和1号i2c
i2c_0 = machine.I2C(0, sda=sda_0, scl=scl_0, freq=400000)
i2c_1 = machine.I2C(1, sda=sda_1, scl=scl_1, freq=400000)

print('Scan i2c bus...')
devices_0 = i2c_0.scan()
devices_1 = i2c_1.scan()

i2c_no = 1

for devices in [devices_0, devices_1]:
    print("I2C_",i2c_no,":",sep='')
    i2c_no += 1

    if len(devices) == 0:
        print("No i2c device !")
    else:
        print('i2c devices found:',len(devices))
        
    for device in devices:
        print("Decimal address: ",device," | Hexa address: ",hex(device))
