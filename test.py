from pycomm3 import CIPDriver

PF525_IP = "192.168.1.11"

PARAM_NUM = 41      # N41
BIT_NUM = 1         # N41.1 → bit 1
SET_BIT = True      # True = turn bit on, False = turn bit off

with CIPDriver(PF525_IP) as drive:
    print("Connected to PowerFlex 525")

    # ---------- READ ----------
    read_resp = drive.generic_message(
        service=0x0E,           # Get_Attribute_Single
        class_code=0x93,        # Parameter Object
        instance=PARAM_NUM,
        attribute=1
    )

    # pycomm3 returns Tag objects
    if read_resp.error is not None:
        print("Read failed:", read_resp.error)
        exit()

    current_val = int.from_bytes(read_resp.value, byteorder='little', signed=True)
    print(f"Current N{PARAM_NUM} value:", current_val)

    # --- CALCULATE NEW VALUE ---
    mask = 1 << BIT_NUM

    if SET_BIT:
        new_val = current_val | mask
    else:
        new_val = current_val & ~mask

    print(f"Writing new value {new_val} to N{PARAM_NUM} (bit {BIT_NUM} {'set' if SET_BIT else 'cleared'})")

    # --- WRITE THE VALUE BACK ---
    write_resp = drive.generic_message(
        service=0x4,                 # Write Data
        class_code=0x93,
        instance=PARAM_NUM,
        attribute=1,
        request_data=new_val.to_bytes(2, 'little', signed=True),
        connected=True
    )

    print("Write Response:", write_resp)

print("Done.")
