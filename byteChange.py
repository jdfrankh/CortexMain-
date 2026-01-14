def get_high_byte( value: int) -> bytes:
    """Extracts the high byte and returns it as a bytes object."""
    # Shift right 8 bits, then convert to a single byte
    high_byte_int = (value >> 8) & 0xFF
    print(bytes([high_byte_int]))
    return bytes([high_byte_int])

def get_low_byte( value: int) -> bytes:
    """Extracts the low byte and returns it as a bytes object."""
    # Mask for the low 8 bits, then convert to a single byte
    low_byte_int = value & 0xFF
    print(bytes([low_byte_int]))
    return bytes([low_byte_int])

# --- How it looks in your packet assembly ---
# Note: Ensure self.speed is an integer (e.g., 6000 for 60.00Hz)
speed = 6000 

prepControls2 = (
    b"\x07\x4D\x00\x31\x55\x8b\x09\x0f\x00\x03\xe9\x67\x00\x00\x03\x00\x00\x24\x4E\x34\x31\x3A\x30\x00\x99\x09\x07\x42\x00\x00\x00\x00" 
    + get_low_byte(speed) 
    + get_high_byte(speed)
)

print(prepControls2)