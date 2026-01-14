#!/usr/bin/env python3

from pycomm3 import CIPDriver, Services, SINT, INT
import struct
import time
from pymodbus.client import ModbusTcpClient
import string

# -------------------------------------------------------------
# PowerFlex 525 Parameter Access via CIP Explicit Messaging
# Class Code: 0x93 (DPI Parameter Object)
# Attribute: 9 = Value
# Instance = Parameter Number (1,2,3,...)
# -------------------------------------------------------------

PF525_CLASS = 0x93
PF525_ATTRIBUTE_VALUE = 3

PARAM_NUM = 41      # N41
BIT_NUM = 1         # N41.1 → bit 1
SET_BIT = True      # True = turn bit on, False = turn bit off

class PowerFlex525:


    PARAM_FREQ_CMD = 1       # Output frequency (Hz)
    PARAM_COMMAND_FREQ = 2 # Commanded frequency (Hz)
    PARAM_OUTPUT_CURRENT = 3 # Output current (A)
    PARAM_OUTPUT_VOLTAGE = 4 # Output voltage (V)
    PARAM_DC_BUS_VOLTAGE = 5 # DC bus voltage (V)
    PARAM_OUTPUT_RPM = 15 # Output speed (RPM)
    PARAM_OUTPUT_POWER = 16 # Output power (kW)

    PARAM_NP_VOLTS = 31
    PARAM_NP_HZ =32
    PARAM_OL_CURRENT = 33
    PARAM_NP_FLA =34
    PARAM_NP_POLES=35
    PARAM_NP_POWER=36

    PARAM_AUTOTUNE = 40

    PARAM_START_SOURCE = 46 # Set to Ethernet IP to drive using the script (5)
    PARAM_SPEED_REF = 47 # Set to Ethernet IP (15)

    PARAM_ACCEL_TIME = 41 #Correlates to the proper parameter number on CCW
    PARAM_DECEL_TIME = 42
    
    toggleState = False
    #speed = 0

    def __init__(self, ip):
        self.ip = ip
        self.drive_path = ip
        self.session = None
        self.speed = 0
        self.toggleState = False

    def setSpeed(self, var):
        #print(self.speed)
        self.speed = var

        if self.toggleState:
            self.write_PCCC_param(self.toggleState)

    def get_high_byte(self, value: int) -> str:
        """
        Extracts the high byte (upper 8 bits) as an integer (0-255).
        Example: 0x1234 (4660) -> 0x12 (18)
        """
        # Right shift 8 bits to move the top byte to the bottom

        #print("High: ", bytes([((value * 100) >> 8 )& 0xFF]))
        return bytes([((value * 100) >> 8 )& 0xFF])

    def get_low_byte(self, value: int) -> str:
        """
        Extracts the low byte (lower 8 bits) as an integer (0-255).
        Example: 0x1234 (4660) -> 0x34 (52)
        """
        # Mask with 0xFF to keep only the bottom 8 bits
        #print("Low: ", bytes([(value * 100)& 0xFF]))
        return bytes([(value* 100)& 0xFF])


    def connect(self):
        print(f"Connecting to PowerFlex525 at {self.ip} ...")
        self.session = CIPDriver(self.drive_path)
        self.session.open()
        print("Connected.")

    def disconnect(self):
        if self.session:
            print("Closing connection...")
            self.session.close()
            print("Disconnected.")

    def write_param_diagnostic(self, session, param_number, value, class_code=0x93, attribute=9, timeout=5.0):
        """
        Attempt to write a parameter and print detailed diagnostics.
        session: open CIPDriver session
        param_number: parameter instance #
        value: numeric value to write (float or int)
        """
        # 1) Read the current raw value so we know expected size/type
        try:
            read_resp = self.session.generic_message(
                service=Services.get_attribute_single,
                class_code=class_code,
                instance=param_number,
                attribute=attribute,
                timeout=timeout
            )
        except Exception as e:
            print(f"[diag] Read failed before write: {e}")
            read_resp = None

        #print(f"[diag] read_resp: {read_resp}")
        raw = getattr(read_resp, 'value', None)

        # Try to infer preferred format
        candidates = []
        if isinstance(raw, (bytes, bytearray)):
            L = len(raw)
            #print(f"[diag] existing raw length={L}")
            if L == 4:
                candidates.append(('REAL32', struct.pack('<f', float(value))))
            if L == 2:
                # signed 16-bit
                candidates.append(('INT16', struct.pack('<h', int(value))))
                candidates.append(('UINT16', struct.pack('<H', int(value) & 0xFFFF)))
            # always offer a 4-byte fallback too
            candidates.append(('REAL32_fallback', struct.pack('<f', float(value))))
        else:
            # unknown raw; try REAL then INT16
            candidates = [('REAL32', struct.pack('<f', float(value))),
                        ('INT16', struct.pack('<h', int(value)))]

        # Attempt writes, show the response
        for tag, payload in candidates:
            try:
            #    print(f"[diag] Trying write as {tag}. payload={payload.hex()}")
                write_resp = self.session.generic_message(
                    service=Services.set_attribute_single,
                    class_code=class_code,
                    instance=param_number,
                    attribute=attribute,
                    request_data=payload,
                    timeout=timeout
                )
            #    print(f"[diag] write_resp: {write_resp}")
                # print possible properties
            #    print("dir(write_resp):", dir(write_resp))
            #    print("write_resp.value:", getattr(write_resp, 'value', None))
            #    print("write_resp.status:", getattr(write_resp, 'status', None))
            #    print("write_resp.error_text:", getattr(write_resp, 'error_text', None))
            except Exception as e:
            #    print(f"[diag] write attempt ({tag}) raised exception: {e}")
                write_resp = None

            # read back and show result
            """"
            try:
                time.sleep(0.2)
                verify = self.session.generic_message(
                    service=Services.get_attribute_single,
                    class_code=class_code,
                    instance=param_number,
                    attribute=attribute,
                    timeout=timeout
                )
                print(f"[diag] verify read after {tag}: {getattr(verify,'value',None)}")
            except Exception as e:
                print(f"[diag] verify read failed after {tag}: {e}")
            """
    # -------------------------------------------------------------
    # Read parameter value
    # -------------------------------------------------------------
    def read_param(self, param_number, divideBy = 1):
        try:
            response = self.session.generic_message(
                service=Services.get_attribute_single,
                class_code=PF525_CLASS,
                instance=param_number,        # Parameter #
                attribute=b'\x09',
                data_type=INT
            )

            raw = response.value

            # PowerFlex returns values as REAL (float) encoded in bytes
            if isinstance(raw, bytes) and len(raw) == 4:
                val = struct.unpack('<f', raw)[0]
            else:
                val = raw

          #  print("Raw: ", raw)
          #  print("Value:", val )
            
            return val/divideBy

        except Exception as e:
            print(f"ERROR reading parameter {param_number}: {e}")
            return 0


    def read_PCCC_param(self, param_number):
        try:
            # Build a PCCC-style request payload that matches the captured message.
            # Observed request pattern: 0x29 <param lo> <param hi> 0x00 0x00

            #For Start PCCCC
            request_data = b"\x07\x4D\x00\xE8\x46\xF1\x30\x0F\x00\x32\x8B\x68\x00\x00\x03\x00\x00\x24\x4E\x34\x31\x3A\x30\x00\x03\x00" # + struct.pack('<H', int(param_number)) + b"\x00\x00"

            response = self.session.generic_message(
                service=0x4b,            # CIP service used for this drive/capture
                class_code=103,          # PCCC related class
                instance=1,
                request_data=request_data
            )

            raw = getattr(response, 'value', None)
            print("[PCCC] raw response:", raw)

            # If we received bytes, show a hex and int dump to mimic the capture view
            if isinstance(raw, (bytes, bytearray)):
                ints = list(raw)
                hex_dump = ' '.join(f"{b:02x}" for b in ints)
                print("[PCCC] bytes:", ints)
                print("[PCCC] hex:", hex_dump)

                # Try to interpret first 4 bytes as a little-endian REAL (float)
                parsed_float = None
                if len(raw) >= 4:
                    try:
                        parsed_float = struct.unpack('<f', raw[0:4])[0]
                        print("[PCCC] float(first4):", parsed_float)
                    except Exception:
                        parsed_float = None

                
                # Return the raw bytes (callers can inspect) but also provide parsed_float
                return {'raw': raw, 'ints': ints, 'hex': hex_dump, 'float': parsed_float}

            # Non-bytes response: return as-is
            return raw

        except Exception as e:
            print(f"ERROR reading parameter {param_number}: {e}")
            return None


    def printResponse(self, response):
            raw = getattr(response, 'value', None)
            #print("[PCCC] raw response:", raw)

            # If we received bytes, show a hex and int dump to mimic the capture view
            if isinstance(raw, (bytes, bytearray)):
                ints = list(raw)
                hex_dump = ' '.join(f"{b:02x}" for b in ints)
                #print("[PCCC] bytes:", ints)
                #print("[PCCC] hex:", hex_dump)

                # Try to interpret first 4 bytes as a little-endian REAL (float)
                parsed_float = None
                """
                if len(raw) >= 4:
                    try:
                        parsed_float = struct.unpack('<f', raw[0:4])[0]
                        print("[PCCC] float(first4):", parsed_float)
                    except Exception:
                        parsed_float = None

                """
                # Return the raw bytes (callers can inspect) but also provide parsed_float
                return {'raw': raw, 'ints': ints, 'hex': hex_dump, 'float': parsed_float}

            # Non-bytes response: return as-is
            return raw


    def prepControls(self):

        try:

            prepControls1 = b"\x07\x4D\x00\x31\x55\x8b\x09\x0f\x00\x03\xe9\x67\x00\x00\x01\x00\x00\x24\x4E\x34\x32\x3A\x33\x00\x99\x09\x03\x42\x05\x00" # + struct.pack('<H', int(param_number)) + b"\x00\x00"
            prepControls2 = b"\x07\x4D\x00\x31\x55\x8b\x09\x0f\x00\x03\xe9\x67\x00\x00\x03\x00\x00\x24\x4E\x34\x31\x3A\x30\x00\x99\x09\x07\x42\x00\x00\x00\x00\x00\x00" #+ self.get_low_byte(self.speed) + self.get_high_byte(self.speed) # + struct.pack('<H', int(param_number)) + b"\x00\x00"

            
            response1 = self.session.generic_message(
                    service=0x4b, #0x4b           # CIP service used for this drive/capture
                    class_code=103,          # PCCC related class
                    instance=1,
                    request_data=prepControls1
                )

            response2 = self.session.generic_message(
                    service=0x4b, #0x4b           # CIP service used for this drive/capture
                    class_code=103,          # PCCC related class
                    instance=1,
                    request_data=prepControls2
                )        

            self.printResponse(response1)
            self.printResponse(response2)
            self.printResponse(response2)


        except Exception as e:
            print(f"ERROR reading parameter: {e}")
            return None

    def write_PCCC_param(self, toggleState):
        print("Write param")
        for i in range(20):

            try:
                # Build a PCCC-style request payload that matches the captured message.
                # Observed request pattern: 0x29 <param lo> <param hi> 0x00 0x00

                

                if(toggleState):
                #For Start PCCCC
                    request_data1 = b"\x07\x4D\x00\x31\x55\x8b\x09\x0f\x00\x6f\x91\x67\x00\x00\x03\x00\x00\x24\x4E\x34\x31\x3A\x30\x00\x99\x09\x07\x42\x02\x00\x00\x00" + self.get_low_byte(self.speed) + self.get_high_byte(self.speed)  # + struct.pack('<H', int(param_number)) + b"\x00\x00"
                    request_data2 = b"\x07\x4D\x00\x31\x55\x8b\x09\x0f\x00\x6f\x91\x67\x00\x00\x03\x00\x00\x24\x4E\x34\x31\x3A\x30\x00\x99\x09\x07\x42\x02\x00\x00\x00" + self.get_low_byte(self.speed) + self.get_high_byte(self.speed)  # + struct.pack('<H', int(param_number)) + b"\x00\x00"
                    request_data3 = b"\x07\x4D\x00\x31\x55\x8b\x09\x0f\x00\x6f\x91\x67\x00\x00\x03\x00\x00\x24\x4E\x34\x31\x3A\x30\x00\x99\x09\x07\x42\x00\x00\x00\x00" + self.get_low_byte(self.speed) + self.get_high_byte(self.speed) 
                else:
                    request_data1 = b"\x07\x4D\x00\x31\x55\x8b\x09\x0f\x00\x6f\x91\x67\x00\x00\x03\x00\x00\x24\x4E\x34\x31\x3A\x30\x00\x99\x09\x07\x42\x09\x00\x00\x00" + self.get_low_byte(self.speed) + self.get_high_byte(self.speed) # + struct.pack('<H', int(param_number)) + b"\x00\x00"
                    request_data2 = b"\x07\x4D\x00\x31\x55\x8b\x09\x0f\x00\x6f\x91\x67\x00\x00\x03\x00\x00\x24\x4E\x34\x31\x3A\x30\x00\x99\x09\x07\x42\x09\x00\x00\x00" + self.get_low_byte(self.speed) + self.get_high_byte(self.speed) # + struct.pack('<H', int(param_number)) + b"\x00\x00"
                    request_data3 = b"\x07\x4D\x00\x31\x55\x8b\x09\x0f\x00\x6f\x91\x67\x00\x00\x03\x00\x00\x24\x4E\x34\x31\x3A\x30\x00\x99\x09\x07\x42\x00\x00\x00\x00" + self.get_low_byte(self.speed) + self.get_high_byte(self.speed) 
                
                self.toggleState = toggleState
                response1 = self.session.generic_message(
                    service=0x4b, #0x4b           # CIP service used for this drive/capture
                    class_code=103,          # PCCC related class
                    instance=1,
                    request_data=request_data1
                )

                response2 = self.session.generic_message(
                    service=0x4b, #0x4b           # CIP service used for this drive/capture
                    class_code=103,          # PCCC related class
                    instance=1,
                    request_data=request_data2
                )

                response3 = self.session.generic_message(
                    service=0x4b, #0x4b           # CIP service used for this drive/capture
                    class_code=103,          # PCCC related class
                    instance=1,
                    request_data=request_data3
                )

                for i in range(10):
                    self.printResponse(response1)  
                    self.printResponse(response1) 
                # self.printResponse(response1)   
                    self.printResponse(response2)   
                    self.printResponse(response3)       
    
    

            except Exception as e:
                print(f"ERROR reading parameter: {e}")
                return None


    def calibrate(self):
        # Example calibration routine (if applicable)
        print("Starting calibration...")
        self.write_param(self.PARAM_AUTOTUNE, 1.0)  # Start autotune
        time.sleep(1)
        print("Calibration command sent.")


# -------------------------------------------------------------
# Example usage
# -------------------------------------------------------------



if __name__ == "__main__":

    DRIVE_IP = "192.168.1.15"   # <<<<< CHANGE THIS

    pf = PowerFlex525(DRIVE_IP)
    pf.connect()

    #pf.write_param_diagnostic(pf.session, pf.PARAM_START_SOURCE)
    
    try:
        """    
        pf.prepControls()

        pf.write_PCCC_param(True)

        pf.write_PCCC_param(False)

        pf.write_PCCC_param(True)
      #  print("Discovering devices on network...")
      #  print(CIPDriver.discover())
        try:
            
            while(True):
                pf.write_PCCC_param(True)
                print("\nReading parameters:")
                busVoltage = pf.read_param(pf.PARAM_DC_BUS_VOLTAGE)
                accel = pf.read_param(pf.PARAM_ACCEL_TIME, 100)
                decel = pf.read_param(pf.PARAM_DECEL_TIME, 100)
                freq = pf.read_param(pf.PARAM_FREQ_CMD, 100)

                print(f"DC Bus Voltage: {busVoltage} V" )
                print(f"Accel Time: {accel} sec")
                print(f"Decel Time: {decel} sec")
                print(f"Output Frequency: {freq} Hz")
                time.sleep(1)

        except KeyboardInterrupt:
            exit(0)
        """
        # Example write
     #   print("\nWriting new Accel Time = .02 sec ...")
     #   pf.write_param(pf.PARAM_ACCEL_TIME, 50.0)
        pf.write_param_diagnostic(pf.session, pf.PARAM_ACCEL_TIME, 25.0) 
     #   time.sleep(0.5)

        # Confirm write succeeded
     #   accel = pf.read_param(pf.PARAM_ACCEL_TIME)
      #  print(f"New Accel Time: {accel} sec")
        
        print("-----------------------------------")

       # print("Attempt to access PCCC object ")

        #pf.write_param_diagnostic(pf.session,  41, 1,103,0)
       
        
        
       # for i in range(40):
       #     pf.prepControls()

       #     print("---------------------------------------------")

       #     pf.write_PCCC_param(True)
       #     print("---------------------------------------------")
       #     time.sleep(3)

       #     pf.write_PCCC_param(False)
       #     time.sleep(1)
       # param = pf.read_PCCC_param(41)
       # print(f"N41 PCCC read: {param}")

        """
        with CIPDriver('192.168.1.11') as drive:  # PowerFlex IP address

            # 1. Build output assembly payload (4 bytes control, 4 bytes speed)
            # Control Word bits:
            # 0 = Stop
            # 1 = Start/Run Forward
            control_word = 0x0001  # Run Forward
            
            speed_ref = 2000  # 20.00 Hz (PowerFlex uses 0.01 Hz units)

            # Build 4-byte payload: control word + speed reference
           # payload = control_word.to_bytes(2, 'little') + speed_ref.to_bytes(2, 'little')

            # Send write request to Output Assembly 21
            response = drive.generic_message(
                class_code=0x04,      # Assembly object
                instance=1,          # Output Assembly 21
                attribute=2,       # Data attribute
                service=0x0E        # Write Data service
              #  request_data=payload,

            )

            print("Response:", response)
        
        """
        """
        ip = "192.168.1.11"  # update this

        with CIPDriver(ip) as drive:
            print("Connected.")

            # Query Assembly Object List
            for instance in range(1, 50):
                try:
                    resp = drive.generic_message(
                        class_code=0x04,     # Assembly Object
                        instance=instance,   # Try each instance
                        attribute=0x03,      # Data
                        service=0x0E,        # Get_Attribute_Single
                        data_type=None
                    )
                    print(f"Instance {instance}: EXISTS (Length={len(resp.value)})")
                except Exception as e:
                    pass

            print("Done.")
            """


    
        

    finally:
        pf.disconnect()
