"""
Simple GUI menu with several combo boxes, numeric input boxes, and Start/Stop buttons.
Saved at: TestBench_Software/menu_gui.py

This is a lightweight Tkinter-based GUI so it should run without extra requirements.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, DoubleVar

import csv
import subprocess
import re
from AB525 import PowerFlex525
from pylogix import PLC
import threading
import time
import math
import temperatureCalculation

# Matplotlib for plotting
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


#pf.connect()



class CalibrationGUI:

    totalHeatLoss = 0
    calculator = temperatureCalculation.TemperatureCalculation()

    """
    SurfaceArea = .02841 #0.005615 # Cooling surface m^2 .044884
    StatorResistance = 3.71
    TorqueRequiredForMotor = .257
    WeightActiveParts = 1.42/2 #kg  #No need for tuning
    SpecificHeat = .0005 #J/kg/degree
    TorqueConstant = .71 #Nm/A
    #/kg
    SpecificHeatDisipation = 541.52 #J/s/m^2/degree diff
    InitalTemp = 16 #degree C
    AmbientTemp = 25 #degree C
    

    currentTemperature = InitalTemp
    """
    curr_t = 0
    start_time_update  = None
    prevTime = 0

    def __init__(self, master: tk.Tk):
        

        self.master = master
        master.title("Powerflex525 Calibration Menu")
        master.geometry("760x720")
        DRIVE_IP = "000.000.0.00"   # <<<<< CHANGE THIS
        pf = PowerFlex525(DRIVE_IP)
        motorOn = False
        # Menubar
        menubar = tk.Menu(master)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=master.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        master.config(menu=menubar)

        # Frame for controls (add external padding so widgets don't stick to window edges)
        frm = ttk.Frame(master, padding=12)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        firstRow = 0
        # Comboboxes (left column: col 0 / 1)
        ttk.Label(frm, text="Mode:").grid(row=firstRow, column=0, sticky=tk.W, pady=4, padx=4)
        self.mode_cb = ttk.Combobox(frm, values=["Jog"], state="readonly")
        self.mode_cb.current(0)
        self.mode_cb.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow+= 1
        ttk.Label(frm, text="Interface:").grid(row=firstRow, column=0, sticky=tk.W, pady=4, padx=4)
        # Replace combobox with a Scan button that finds Ethernet IPv4 addresses
        self.if_btn = ttk.Button(frm, text="Scan Ethernet IPs", command=self.on_scan)
        self.if_btn.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)
        # Display chosen interface/ip
        self.interface_var = tk.StringVar(value="(none)")
        ttk.Label(frm, textvariable=self.interface_var).grid(row=1, column=2, sticky=tk.W, padx=6, pady=4)

        firstRow += 1
        ttk.Label(frm, text="Profile:").grid(row=firstRow, column=0, sticky=tk.W, pady=4, padx=4)
        self.profile_cb = ttk.Combobox(frm, values=["Default", "High Power", "Eco"], state="readonly")
        self.profile_cb.current(0)
        self.profile_cb.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)
        
        firstRow += 1
        # Main numeric fields (second column: col 2 / 3)
        ttk.Label(frm, text="Voltage (V):").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.voltage_var = tk.StringVar(value="0.0")
        self.voltage_entry = ttk.Entry(frm, textvariable=self.voltage_var, state = "readonly")
        self.voltage_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1
        ttk.Label(frm, text="Current (A):").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.current_var = tk.StringVar(value="0.0")
        self.current_entry = ttk.Entry(frm, textvariable=self.current_var, state = "readonly")
        self.current_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1
        ttk.Label(frm, text="RPM :").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.rpm_var = tk.StringVar(value="0.0")
        self.rpm_entry = ttk.Entry(frm, textvariable=self.rpm_var, state = "readonly")
        self.rpm_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1
        ttk.Label(frm, text="Input Power: (kW)").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.inputPower_var = tk.StringVar(value="0.0")
        self.inputPower_entry = ttk.Entry(frm, textvariable=self.inputPower_var, state = "readonly")
        self.inputPower_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1
        ttk.Label(frm, text="Bus Voltage: (V)").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.busVoltage_var = tk.StringVar(value="0.0")
        self.busVoltage_entry = ttk.Entry(frm, textvariable=self.busVoltage_var, state = "readonly")
        self.busVoltage_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1
        ttk.Label(frm, text="--------------------------------").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)

        firstRow += 1
        ttk.Label(frm, text="Calculated Output Toruqe: (Nm)").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.outTorque_var = tk.StringVar(value="0.0")
        self.outTorque_entry = ttk.Entry(frm, textvariable=self.outTorque_var, state = "readonly")
        self.outTorque_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1
        ttk.Label(frm, text="Calculated Shaft Power (kW)").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.outPower_var = tk.StringVar(value="0.0")
        self.outPower_entry = ttk.Entry(frm, textvariable=self.outPower_var, state = "readonly")
        self.outPower_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1
        ttk.Label(frm, text="Efficiency %").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.effi_var = tk.StringVar(value="0.0")
        self.effi_entry = ttk.Entry(frm, textvariable=self.effi_var, state = "readonly")
        self.effi_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1
        ttk.Label(frm, text="Power Loss (kW)").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.loss_var = tk.StringVar(value="0.0")
        self.loss_entry = ttk.Entry(frm, textvariable=self.loss_var, state = "readonly")
        self.loss_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1

        ttk.Label(frm, text="I2R Losses").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.i2r_var = tk.StringVar(value="0.0")
        self.i2r_entry = ttk.Entry(frm, textvariable=self.i2r_var, state = "readonly")
        self.i2r_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1

        ttk.Label(frm, text="Time to max Temp:").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4) # Speed losses
        self.speedLoss_var = tk.StringVar(value="0.0")
        self.speedLoss_entry = ttk.Entry(frm, textvariable=self.speedLoss_var, state = "readonly")
        self.speedLoss_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1

        ttk.Label(frm, text="Time Constant").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.timeConst_var = tk.StringVar(value="0.0")
        self.timeConst_entry = ttk.Entry(frm, textvariable=self.timeConst_var, state = "readonly")
        self.timeConst_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1

        ttk.Label(frm, text="Max Temp Rise (C)").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.maxTempRise_var = tk.StringVar(value="0.0")
        self.maxTempRise_entry = ttk.Entry(frm, textvariable=self.maxTempRise_var, state = "readonly")
        self.maxTempRise_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1

        ttk.Label(frm, text="Possible Temperature (C)").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.temp_var = tk.StringVar(value="0.0")
        self.temp_entry = ttk.Entry(frm, textvariable=self.temp_var, state = "readonly")
        self.temp_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)

        firstRow += 1
        
        ttk.Label(frm, text="Commanded Frequency:").grid(row=firstRow, column=0, sticky=tk.W, padx=6, pady=4)
        self.v1 = DoubleVar()
        self.v1_entry = ttk.Scale( frm, variable = self.v1, from_ = 0, to = 150, orient = tk.HORIZONTAL, command=self.updateVariables()).grid(row=firstRow, column=1, sticky=tk.W, padx=6, pady=4)
        firstRow += 1

        self.freq_var = tk.StringVar(value="0.0")
        self.freq_entry = ttk.Entry(frm, textvariable=self.freq_var, state = "readonly")
        self.freq_entry.grid(row=firstRow, column=1, sticky=tk.EW, padx=6, pady=4)
        
        secondRow = 3
        ttk.Label(frm, text="Nameplate Volts:").grid(row=secondRow, column=2, sticky=tk.W, padx=6, pady=4)
        self.NPVolts_var = tk.StringVar(value="0")
        self.NPVolts_entry = ttk.Entry(frm, textvariable=self.NPVolts_var)
        self.NPVolts_entry.grid(row=secondRow, column=3, sticky=tk.EW, padx=6, pady=4)

        secondRow += 1
        ttk.Label(frm, text="Nameplate Hertz:").grid(row=secondRow, column=2, sticky=tk.W, padx=6, pady=4)
        self.NPHz_var = tk.StringVar(value="0")
        self.NPHz_entry = ttk.Entry(frm, textvariable=self.NPHz_var)
        self.NPHz_entry.grid(row=secondRow, column=3, sticky=tk.EW, padx=6, pady=4)

        # Additional calibration fields (second column continuing)
        secondRow += 1
        ttk.Label(frm, text="OL Current:").grid(row=secondRow, column=2, sticky=tk.W, padx=6, pady=4)
        self.ol_current_var = tk.StringVar(value="0.0")
        ttk.Entry(frm, textvariable=self.ol_current_var).grid(row=secondRow, column=3, sticky=tk.EW, padx=6, pady=4)
        secondRow += 1

        ttk.Label(frm, text="Nameplate FLA:").grid(row=secondRow, column=2, sticky=tk.W, padx=6, pady=4)
        self.nameplate_fla_var = tk.StringVar(value="0.0")
        ttk.Entry(frm, textvariable=self.nameplate_fla_var).grid(row=secondRow, column=3, sticky=tk.EW, padx=6, pady=4)
        secondRow += 1

        ttk.Label(frm, text="Number of Poles:").grid(row=secondRow, column=2, sticky=tk.W, padx=6, pady=4)
        self.num_poles_var = tk.StringVar(value="0")
        ttk.Entry(frm, textvariable=self.num_poles_var).grid(row=secondRow, column=3, sticky=tk.EW, padx=6, pady=4)
        secondRow += 1

        ttk.Label(frm, text="Nameplate RPM:").grid(row=secondRow, column=2, sticky=tk.W, padx=6, pady=4)
        self.nameplate_rpm_var = tk.StringVar(value="0")
        ttk.Entry(frm, textvariable=self.nameplate_rpm_var).grid(row=secondRow, column=3, sticky=tk.EW, padx=6, pady=4)
        secondRow += 1

        ttk.Label(frm, text="Nameplate Power:").grid(row=secondRow, column=2, sticky=tk.W, padx=6, pady=4)
        self.nameplate_power_var = tk.StringVar(value="0")
        ttk.Entry(frm, textvariable=self.nameplate_power_var).grid(row=secondRow, column=3, sticky=tk.EW, padx=6, pady=4)
        secondRow += 1

        ttk.Label(frm, text="---------------------------------").grid(row=secondRow, column=2, sticky=tk.W, padx=6, pady=4)
        secondRow += 1

        #irVolt_var

        ttk.Label(frm, text="IR Voltage:").grid(row=secondRow, column=2, sticky=tk.W, padx=6, pady=4)
        self.irVolt_var = tk.StringVar(value="0.0")
        ttk.Entry(frm, textvariable=self.irVolt_var).grid(row=secondRow, column=3, sticky=tk.EW, padx=6, pady=4)
        secondRow += 1

        ttk.Label(frm, text="IXd Voltage:").grid(row=secondRow, column=2, sticky=tk.W, padx=6, pady=4)
        self.ixdVolt_var = tk.StringVar(value="0.0")
        ttk.Entry(frm, textvariable=self.ixdVolt_var).grid(row=secondRow, column=3, sticky=tk.EW, padx=6, pady=4)
        secondRow += 1

        ttk.Label(frm, text="IXq Voltage:").grid(row=secondRow, column=2, sticky=tk.W, padx=6, pady=4)
        self.ixqVolt_var = tk.StringVar(value="0.0")
        ttk.Entry(frm, textvariable=self.ixqVolt_var).grid(row=secondRow, column=3, sticky=tk.EW, padx=6, pady=4)
        secondRow += 1

        ttk.Label(frm, text="BEMF Voltage:").grid(row=secondRow, column=2, sticky=tk.W, padx=6, pady=4)
        self.bemf_var = tk.StringVar(value="0")
        ttk.Entry(frm, textvariable=self.bemf_var).grid(row=secondRow, column=3, sticky=tk.EW, padx=6, pady=4)
        secondRow += 1



        # Third column (new) for extra fields (col 4 / 5)
        extra_row = 0
        ttk.Label(frm, text="Extra Param A:").grid(row=extra_row, column=4, sticky=tk.W, padx=6, pady=4)
        self.extra_a_var = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.extra_a_var).grid(row=extra_row, column=5, sticky=tk.EW, padx=6, pady=4)
        extra_row += 1

        ttk.Label(frm, text="Extra Param B:").grid(row=extra_row, column=4, sticky=tk.W, padx=6, pady=4)
        self.extra_b_var = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.extra_b_var).grid(row=extra_row, column=5, sticky=tk.EW, padx=6, pady=4)
        extra_row += 1

        ttk.Label(frm, text="Extra Param C:").grid(row=extra_row, column=4, sticky=tk.W, padx=6, pady=4)
        self.extra_c_var = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.extra_c_var).grid(row=extra_row, column=5, sticky=tk.EW, padx=6, pady=4)
        extra_row += 1

        ttk.Label(frm, text="Extra Param D:").grid(row=extra_row, column=4, sticky=tk.W, padx=6, pady=4)
        self.extra_d_var = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.extra_d_var).grid(row=extra_row, column=5, sticky=tk.EW, padx=6, pady=4)
        extra_row += 1

        # Buttons (place after the calibration fields). Add Export button above Start/Stop
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=firstRow + 8, column=0, columnspan=6, pady=(18, 0), sticky=tk.EW)

        # Import button above Export
        self.import_btn = ttk.Button(btn_frame, text="Import Drive File", command=self.on_import)
        self.import_btn.grid(row=0, column=0, columnspan=2, padx=8, pady=(0, 8))

        # Export button below Import
        self.export_btn = ttk.Button(btn_frame, text="Export Drive File", command=self.on_export)
        self.export_btn.grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 8))

        # Start/Stop placed on the next row
        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.on_start)
        self.start_btn.grid(row=2, column=0, padx=8)

        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.on_stop, state=tk.NORMAL) #tk.ENABLED
        self.stop_btn.grid(row=2, column=1, padx=8)
        # Graph button
        self.graph_btn = ttk.Button(btn_frame, text="Graph", command=self.open_graph_window)
        self.graph_btn.grid(row=2, column=2, padx=8)

        # Configure column expansion so columns 1, 3 and 5 grow, leaving margins on the sides
        frm.columnconfigure(1, weight=1)
        frm.columnconfigure(3, weight=1)
        frm.columnconfigure(5, weight=1)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(master, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status.pack(side=tk.BOTTOM, fill=tk.X)

    def get_ethernet_ips(self):
        with PLC() as comm:
            devices = comm.Discover()

        # Filter to ethernet-like adapters (case-insensitive)
        return devices#[(a, ip) for (a, ip) in adapters if "ethernet" in a.lower()]
        
    def on_scan(self):
        """Scan for Ethernet IPs and show them in a separate window for selection."""
        results = self.get_ethernet_ips()
        print(results)
        if not results:
            messagebox.showinfo("Scan result", "No Ethernet IPv4 addresses found.")
            return

        top = tk.Toplevel(self.master)
        top.title("Discovered Ethernet IPs")
        top.geometry("480x240")

        lb = tk.Listbox(top, selectmode=tk.SINGLE)
        lb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        for device in results.Value:
            lb.insert(tk.END, f"{device.ProductName} — {device.IPAddress}")

        btns = ttk.Frame(top)
        btns.pack(fill=tk.X, padx=8, pady=(0, 8))

        def choose(ev=None):
            sel = lb.curselection()
            if not sel:
                messagebox.showwarning("No selection", "Please select an address first.")
                return
            text = lb.get(sel[0])
            ip = text.split("—")[-1].strip()
            self.interface_var.set(ip)

            self.pf = PowerFlex525(ip)
            self.pf.connect()

            self.readInitalParams()


            top.destroy()

        ok = ttk.Button(btns, text="OK", command=choose)
        ok.pack(side=tk.LEFT, padx=6)
        cancel = ttk.Button(btns, text="Cancel", command=top.destroy)
        cancel.pack(side=tk.LEFT, padx=6)
        lb.bind("<Double-1>", choose)

    def readInitalParams(self):
        
        self.extra_a_var.set(self.calculator.SpecificHeatDisipation)
        self.extra_b_var.set(self.calculator.SpecificHeat)
        self.extra_c_var.set(self.calculator.SurfaceArea)
        self.extra_d_var.set(self.calculator.TorqueConstant)
        
        self.NPVolts_var.set(self.pf.read_param(31))
        self.NPHz_var.set(self.pf.read_param(32))
        self.ol_current_var.set(self.pf.read_param(33) / 10)
        self.nameplate_fla_var.set(self.pf.read_param(34) / 10)
        self.num_poles_var.set(self.pf.read_param(35))
        self.nameplate_rpm_var.set(self.pf.read_param(36))
        self.nameplate_power_var.set(self.pf.read_param(37) / 100)

        self.irVolt_var.set(self.pf.read_param(501) / 100)
        self.ixdVolt_var.set(self.pf.read_param(502) / 100)
        self.ixqVolt_var.set(self.pf.read_param(503) / 100)
        self.bemf_var.set(self.pf.read_param(504) / 10)


    def on_export(self):
        """Export current drive/calibration fields to a CSV file chosen by the user."""
        fname = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not fname:
            return
        try:
            with open(fname, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                headers = [
                    "Mode",
                    "Interface",
                    "Profile",
                    "Voltage",
                    "Current",
                    "Duration",
                    "OL Current",
                    "Nameplate FLA",
                    "Num Poles",
                    "Nameplate RPM",
                    "Extra A",
                    "Extra B",
                    "Extra C",
                    "Extra D",
                ]
                values = [
                    self.mode_cb.get(),
                    self.interface_var.get(),
                    self.profile_cb.get(),
                    self.voltage_var.get(),
                    self.current_var.get(),
                    self.duration_var.get(),
                    self.ol_current_var.get(),
                    self.nameplate_fla_var.get(),
                    self.num_poles_var.get(),
                    self.nameplate_rpm_var.get(),
                    self.extra_a_var.get(),
                    self.extra_b_var.get(),
                    self.extra_c_var.get(),
                    self.extra_d_var.get(),
                ]
                writer.writerow(headers)
                writer.writerow(values)
            messagebox.showinfo("Exported", f"Drive file saved to:\n{fname}")
        except Exception as e:
            messagebox.showerror("Export failed", f"Could not save file:\n{e}")

    def on_import(self):
        """Import drive/calibration fields from a CSV file and populate the form."""
        fname = filedialog.askopenfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not fname:
            return
        try:
            with open(fname, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                if not rows:
                    messagebox.showerror("Import failed", "File is empty")
                    return

                # Determine which row contains values.
                first = rows[0]
                headers = [
                    "Mode",
                    "Interface",
                    "Profile",
                    "Voltage",
                    "Current",
                    "Duration",
                    "OL Current",
                    "Nameplate FLA",
                    "Num Poles",
                    "Nameplate RPM",
                    "Extra A",
                    "Extra B",
                    "Extra C",
                    "Extra D",
                ]

                if any(h in first for h in headers) and len(rows) > 1:
                    values = rows[1]
                else:
                    values = rows[0]

                # Helper to safely get value by index
                def gv(i):
                    try:
                        return values[i]
                    except Exception:
                        return ""

                # Map values into the form (best-effort)
                self.mode_cb.set(gv(0))
                self.interface_var.set(gv(1))
                self.profile_cb.set(gv(2))
                self.voltage_var.set(gv(3))
                self.current_var.set(gv(4))
                self.duration_var.set(gv(5))
                self.ol_current_var.set(gv(6))
                self.nameplate_fla_var.set(gv(7))
                self.num_poles_var.set(gv(8))
                self.nameplate_rpm_var.set(gv(9))
                self.extra_a_var.set(gv(10))
                self.extra_b_var.set(gv(11))
                self.extra_c_var.set(gv(12))
                self.extra_d_var.set(gv(13))

            messagebox.showinfo("Imported", f"Drive file loaded from:\n{fname}")
        except Exception as e:
            messagebox.showerror("Import failed", f"Could not read file:\n{e}")


    def updateVariables(self):

        try:
            

            self.master.after(250, self.updateVariables)
            self.voltage_var.set(float(self.pf.read_param(4))/10)
            self.current_var.set(float(self.pf.read_param(3))/100)
            self.rpm_var.set(float(self.pf.read_param(15))/1)
            self.inputPower_var.set((float(self.voltage_var.get()) * float(self.voltage_var.get())/1000))
            self.busVoltage_var.set(float(self.pf.read_param(5))/1)

            self.outTorque_var.set(float(self.calculator.TorqueConstant * float(self.current_var.get())))
            #self.outTorque_var.set(float(self.TorqueRequiredForMotor))
            self.pf.setSpeed(int(self.v1.get()))

            #self.outPower_var.set(float(5 * float(self.rpm_var.get()) / 9550))
            

            self.freq_var.set(int(self.v1.get()))
            self.outPower_var.set(float(float(self.outTorque_var.get()) * float(self.rpm_var.get()) / 9550))

            try:
                self.effi_var.set( (float(float(self.outPower_var.get()))/ (float(float(self.inputPower_var.get())))) * 100 )
            except ZeroDivisionError:
                self.effi_var.set(float(0))

            self.loss_var.set(float(float(self.inputPower_var.get()) - float(self.outPower_var.get())))

            self.i2r_var.set(float( (float(self.current_var.get()) ** 2) * self.calculator.StatorResistance ) / 1000)
            
            #self.calculator.SpecificHeatDisipation = float( self.extra_a_var.get())
            #self.calculator.SpecificHeat = float( self.extra_b_var.get())

            #self.totalHeatLoss = float(self.i2r_var.get()) + float(self.speedLoss_var.get())
            self.totalHeatLoss = float(self.loss_var.get())  #convert to watts
            

            

            now = time.time()
            if self.start_time_update is None:
                self.start_time_update = now

            self.curr_t = now - self.start_time_update
            #print(self.curr_t)
            seconds = self.curr_t
            diffTime = now - self.prevTime

            self.prevTime = now

            
            self.calculator.UpdateParameters(self.totalHeatLoss, diffTime)
            #timeConstant = self.WeightActiveParts * self.SpecificHeat / self.SurfaceArea * self.SpecificHeatDisipation  
            #maximumTemp = self.totalHeatLoss * 1000 / self.SurfaceArea / self.SpecificHeatDisipation

            #try:
            #    term1 = math.log((self.totalHeatLoss * 1000) - (self.SurfaceArea*self.SpecificHeatDisipation*(maximumTemp - 1)))
            #    term2= ( -1 * math.log(self.totalHeatLoss * 1000))

            #except ValueError:
            #    term1 = 0
            #    term2 = 0

            self.speedLoss_var.set(float(self.calculator.currDeltaTemp)) # Time to max temp -- dt method

            self.timeConst_var.set(float(self.calculator.timeConstant))
            self.maxTempRise_var.set(float(self.calculator.maximumTemp))

            

            
            

            #firstTerm = maximumTemp * (1 - math.exp(-1 * hours/ timeConstant))
            #secondTerm = (self.currentTemperature * math.exp(-1 * hours/ timeConstant))
            #self.currentTemperature = self.curr_t * (self.totalHeatLoss - self.SurfaceArea * self.SpecificHeatDisipation * (self.currentTemperature)) / self.WeightActiveParts
            #print(hours, " " , firstTerm, " " , secondTerm, " " , self.currentTemperature, " ", math.exp(-1 * hours/timeConstant))
            #self.currentTemperature =  firstTerm + secondTerm 
            self.temp_var.set(self.calculator.currentTemperature)

            

            

            
            
            
            #self.effi_var.set(float(self))
        except AttributeError as e:
            print(f"Error: \n{e}")
        

        

    def on_start(self):
        # Parse the main numeric fields (Voltage, Current, Duration). If parsing fails, show error but don't crash.
        try:

            self.pf.write_param_diagnostic(self.pf.session, 44, 15000)
            
            self.pf.write_param_diagnostic(self.pf.session,31, int(float(self.NPVolts_var.get())))
            self.pf.write_param_diagnostic(self.pf.session,32, int(float(self.NPHz_var.get())) )
            self.pf.write_param_diagnostic(self.pf.session,33, float(self.ol_current_var.get()) * 10 )
            self.pf.write_param_diagnostic(self.pf.session,34, float(self.nameplate_fla_var.get()) * 10  )
            self.pf.write_param_diagnostic(self.pf.session,35, int(float(self.num_poles_var.get())) )
            self.pf.write_param_diagnostic(self.pf.session,36, int(float(self.nameplate_rpm_var.get())) )
            self.pf.write_param_diagnostic(self.pf.session,37, float(self.nameplate_power_var.get()) * 100)

            self.pf.write_param_diagnostic(self.pf.session,501, float(self.irVolt_var.get()) * 100)
            self.pf.write_param_diagnostic(self.pf.session,502, float(self.ixdVolt_var.get()) * 100)
            self.pf.write_param_diagnostic(self.pf.session,503, float(self.ixqVolt_var.get()) * 100)
            self.pf.write_param_diagnostic(self.pf.session,504, float(self.bemf_var.get()) * 10)

            self.pf.prepControls()
            self.pf.write_PCCC_param(True)
            self.pf.write_PCCC_param(False)
            self.pf.write_PCCC_param(True)
            

            self.updateVariables()

        
        

        except Exception as e:
            messagebox.showerror("Invalid input", f"Please enter valid numeric values.\n{e}")
            return

        # Read combo selections
        mode = self.mode_cb.get()
        interface = self.interface_var.get()
        profile = self.profile_cb.get()

        # Simulate starting an operation: disable Start, enable Stop
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Running...")
        self.calculator.isMotorOn = True


  
    def on_stop(self):
        self.pf.write_PCCC_param(False)
        self.calculator.isMotorOn = False
        # Simulate stopping: enable Start, disable Stop
        self.start_btn.config(state=tk.NORMAL)
        #self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Stopped")
        print("Stopped by user")
        #messagebox.showinfo("Stopped", "Operation stopped.")

    def open_graph_window(self):
        # Open a separate Toplevel window with two graphs and controls
        GraphWindow(self.master, self)


class GraphWindow:
    def __init__(self, root, parent_gui: CalibrationGUI):
        self.parent = parent_gui
        self.root = tk.Toplevel(root)
        self.root.title("Parameter Graphs")
        # Make the window and plots larger per request
        self.root.geometry("1100x900")

        # Available parameters (map label -> getter)
        self.param_names = [
            "Voltage", "Current", "RPM", "Input Power", "Bus Voltage",
            "Output Torque", "Output Power", "Efficiency", "Power Loss"
        ]

        topfrm = ttk.Frame(self.root, padding=8)
        topfrm.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(topfrm, text="Param 1:").pack(side=tk.LEFT)
        self.cb1 = ttk.Combobox(topfrm, values=self.param_names, state='readonly')
        self.cb1.current(0)
        self.cb1.pack(side=tk.LEFT, padx=6)

        ttk.Label(topfrm, text="Param 2:").pack(side=tk.LEFT)
        self.cb2 = ttk.Combobox(topfrm, values=self.param_names, state='readonly')
        self.cb2.current(1)
        self.cb2.pack(side=tk.LEFT, padx=6)

        ttk.Label(topfrm, text="Param 3:").pack(side=tk.LEFT)
        self.cb3 = ttk.Combobox(topfrm, values=self.param_names, state='readonly')
        self.cb3.current(2)
        self.cb3.pack(side=tk.LEFT, padx=6)

        self.start_btn = ttk.Button(topfrm, text="Start Sampling", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=6)
        self.stop_btn = ttk.Button(topfrm, text="Stop Sampling", command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=6)

        self.export_btn = ttk.Button(topfrm, text="Export Samples", command=self.export_samples)
        self.export_btn.pack(side=tk.LEFT, padx=6)

        # Figure with five subplots (3 user-selectable + combined I2R/SpeedLoss + Temperature)
        self.fig = Figure(figsize=(10, 9), dpi=100)
        # Use 5 rows stacked vertically
        self.ax1 = self.fig.add_subplot(511)
        self.ax2 = self.fig.add_subplot(512)
        self.ax3 = self.fig.add_subplot(513)
        self.ax4 = self.fig.add_subplot(514)  # combined I2R and SpeedLoss
        self.ax5 = self.fig.add_subplot(515)  # temperature

        self.ax1.set_ylabel(self.cb1.get())
        self.ax2.set_ylabel(self.cb2.get())
        self.ax3.set_ylabel(self.cb3.get())
        self.ax4.set_ylabel('I2R / SpeedLoss')
        self.ax5.set_ylabel('Temperature (C)')
        self.ax5.set_xlabel("Time (s)")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Data storage
        self.times = []
        self.data1 = []
        self.data2 = []
        self.data3 = []
        # combined graph series
        self.data_i2r = []
        self.data_speedLoss = []
        # temperature series
        self.data_temp = []

        self.start_time = None
        self.running = False
        self.after_id = None

    def get_value_by_name(self, name: str) -> float:
        # Read value from parent GUI's StringVars (they are updated by updateVariables)
        try:
            if name == "Voltage":
                return float(self.parent.voltage_var.get())
            if name == "Current":
                return float(self.parent.current_var.get())
            if name == "RPM":
                return float(self.parent.rpm_var.get())
            if name == "Input Power":
                return float(self.parent.inputPower_var.get())
            if name == "Bus Voltage":
                return float(self.parent.busVoltage_var.get())
            if name == "Output Torque":
                return float(self.parent.outTorque_var.get())
            if name == "Output Power":
                return float(self.parent.outPower_var.get())
            if name == "Efficiency":
                return float(self.parent.effi_var.get())
            if name == "Power Loss":
                return float(self.parent.loss_var.get())
        except Exception:
            return float('nan')

    def sample(self):
        if not self.running:
            return
        now = time.time()
        if self.start_time is None:
            self.start_time = now
        t = now - self.start_time

        # three user-selectable parameters
        p1 = self.get_value_by_name(self.cb1.get())
        p2 = self.get_value_by_name(self.cb2.get())
        p3 = self.get_value_by_name(self.cb3.get())

        # combined and temperature fixed series
        try:
            p_i2r = float(self.parent.i2r_var.get())
        except Exception:
            p_i2r = float('nan')
        try:
            p_speed = float(self.parent.speedLoss_var.get())
        except Exception:
            p_speed = float('nan')
        try:
            p_temp = float(self.parent.temp_var.get())
        except Exception:
            p_temp = float('nan')

        # append data
        self.times.append(t)
        self.data1.append(p1)
        self.data2.append(p2)
        self.data3.append(p3)
        self.data_i2r.append(p_i2r)
        self.data_speedLoss.append(p_speed)
        self.data_temp.append(p_temp)

        # Update plots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        self.ax5.clear()

        self.ax1.plot(self.times, self.data1, '-b')
        self.ax2.plot(self.times, self.data2, '-r')
        self.ax3.plot(self.times, self.data3, '-g')

        # combined I2R (blue) and SpeedLoss (orange)
        self.ax4.plot(self.times, self.data_i2r, '-b', label='I2R')
        self.ax4.plot(self.times, self.data_speedLoss, '-C1', label='SpeedLoss')
        self.ax4.legend(loc='upper right')

        # temperature
        self.ax5.plot(self.times, self.data_temp, '-m')

        # set labels
        self.ax1.set_ylabel(self.cb1.get())
        self.ax2.set_ylabel(self.cb2.get())
        self.ax3.set_ylabel(self.cb3.get())
        self.ax4.set_ylabel('I2R / SpeedLoss')
        self.ax5.set_ylabel('Temperature (C)')
        self.ax5.set_xlabel('Time (s)')

        # tighten layout and redraw
        try:
            self.fig.tight_layout()
        except Exception:
            pass
        self.canvas.draw_idle()

        # schedule next sample
        self.after_id = self.root.after(500, self.sample)

    def start(self):
        if self.running:
            return
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        # reset data
        self.times = []
        self.data1 = []
        self.data2 = []
        self.data3 = []
        self.data_i2r = []
        self.data_speedLoss = []
        self.data_temp = []
        self.start_time = None
        # ensure parent variables get updated at least once
        try:
            self.parent.updateVariables()
        except Exception:
            pass
        self.sample()

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        if self.after_id:
            try:
                self.root.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def export_samples(self):
        if not self.times:
            messagebox.showwarning("No data", "No samples to export.")
            return
        fname = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv'),('All','*.*')])
        if not fname:
            return
        try:
            with open(fname, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # header includes user-selectable labels and the fixed series
                writer.writerow(['time_s', self.cb1.get(), self.cb2.get(), self.cb3.get(), 'I2R Losses', 'Speed Losses', 'Temperature'])
                for i in range(len(self.times)):
                    t = self.times[i]
                    v1 = self.data1[i] if i < len(self.data1) else ''
                    v2 = self.data2[i] if i < len(self.data2) else ''
                    v3 = self.data3[i] if i < len(self.data3) else ''
                    v_i2r = self.data_i2r[i] if i < len(self.data_i2r) else ''
                    v_speed = self.data_speedLoss[i] if i < len(self.data_speedLoss) else ''
                    v_temp = self.data_temp[i] if i < len(self.data_temp) else ''
                    writer.writerow([t, v1, v2, v3, v_i2r, v_speed, v_temp])
            messagebox.showinfo('Exported', f'Samples saved to:\n{fname}')
        except Exception as e:
            messagebox.showerror('Export failed', f'Could not save file:\n{e}')


if __name__ == "__main__":
    root = tk.Tk()
    app = CalibrationGUI(root)

    root.mainloop()


