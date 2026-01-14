# Modbus RTU RS485 USB Example

This small example demonstrates how to read Modbus registers (RTU) from a device connected through an RS485->USB adapter using pymodbus.

Requirements

- Python 3.8+
- Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Usage examples (PowerShell)

Read 10 holding registers starting at address 0 from unit 1 on COM3:

```powershell
python .\testBench.py --port COM3 --baud 38400 --parity O --unit 1 --type holding --address 0 --count 10
```

Common troubleshooting:

- Ensure the adapter is visible in Device Manager (Windows) and note the COM port.
- Confirm wiring for RS485 A/B and termination if required by your bus.
- Try different parity/baud settings to match the slave device.
- If you get permission denied on Unix, run with sudo or add your user to the dialout group.
