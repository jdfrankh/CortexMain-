#!/usr/bin/env python
import minimalmodbus

minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True

instrument = minimalmodbus.Instrument('COM5', 1) # port name, slave address (in decimal)

instrument.serial.port =  'COM5'         # this is the serial port name
instrument.serial.baudrate = 19200   # Baud
instrument.serial.bytesize = 8
instrument.serial.stopbits = 1
instrument.serial.timeout  = 0.05   # seconds
instrument.debug = True
## Read temperature (PV = ProcessValue) ##
value = instrument.read_registers(0, 2)[1] # Registernumber, number of decimals
#2,2 for speed at second element
#0,2 for torque
print(value)

