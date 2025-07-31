import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import serial
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import queue
import json
import os
from datetime import datetime

# === UART Setup ===
SERIAL_PORT = '/dev/ttyUSB0'  # Change as needed
BAUD_RATE = 115200

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
except serial.SerialException:
    ser = None
    print("⚠️ Could not open serial port.")

# === Constants ===
PREAMBLE = b'OK'
PAYLOAD_SIZE = 28800  # Match DMA_RX_DATA_SIZE from firmware
PACKET_SIZE = 2 + PAYLOAD_SIZE + 1  # "OK" + data + "\n"

# === GUI App ===
class UARTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sonar Experiment Control Panel")
        self.root.geometry("1400x900")

        # Load experiment data
        self.experiments = self.load_experiments()
        self.current_data = []
        self.experiment_title = tk.StringVar()
        self.experiment_title.set("Experiment Title")

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top frame for title and experiment selection
        self.top_frame = tk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, pady=(0, 10))

        # Title entry
        tk.Label(self.top_frame, text="Experiment Title:").pack(side=tk.LEFT)
        self.title_entry = tk.Entry(self.top_frame, textvariable=self.experiment_title, width=30)
        self.title_entry.pack(side=tk.LEFT, padx=(5, 20))

        # Experiment selection
        tk.Label(self.top_frame, text="Phase Experiment:").pack(side=tk.LEFT)
        self.experiment_var = tk.StringVar()
        self.experiment_combo = ttk.Combobox(self.top_frame, textvariable=self.experiment_var,
                                           values=[exp["name"] for exp in self.experiments], width=30)
        self.experiment_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.experiment_combo.bind('<<ComboboxSelected>>', self.on_experiment_selected)

        # Main content frame
        self.content_frame = tk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Chart frame (left side)
        self.chart_frame = tk.Frame(self.content_frame)
        self.chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Plot setup with interactive features
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.ax.set_title("Sonar Profile Data")
        self.ax.set_xlabel("Sample Index")
        self.ax.set_ylabel("Value")
        self.line, = self.ax.plot([], [], color='blue', linewidth=0.5)  # Thinner line for large datasets
        self.ax.set_ylim(0, 255)
        self.ax.grid(True, alpha=0.3)

        # Create canvas with navigation toolbar
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Add navigation toolbar for zoom, pan, etc.
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.chart_frame)
        self.toolbar.update()

        # Control sidebar (right side)
        self.sidebar = tk.Frame(self.content_frame, width=250)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.sidebar.pack_propagate(False)

        self.create_control_sidebar()

        # Queue and thread for UART
        self.data_queue = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self.uart_reader, daemon=True)
        self.thread.start()

        self.update_chart()

    def load_experiments(self):
        """Load experiments from phases.json"""
        try:
            with open('data/phases.json', 'r') as f:
                data = json.load(f)
                return data.get('phases', [])
        except Exception as e:
            print(f"Error loading experiments: {e}")
            return []

    def on_experiment_selected(self, event=None):
        """Handle experiment selection"""
        selected_name = self.experiment_var.get()
        for exp in self.experiments:
            if exp["name"] == selected_name:
                # Update the experiment title with the selected experiment name
                self.experiment_title.set(exp["name"])
                self.send_experiment_phases(exp["data"])
                break

    def send_experiment_phases(self, phases):
        """Send phase values to the device"""
        if not ser or not ser.is_open:
            messagebox.showerror("Error", "Serial port not available")
            return

        # Send new phases
        for i, phase in enumerate(phases):
            if i >= 600:  # Safety check for max 600 phases
                break
            self.send_uart(f"P:{i}:{phase}")

        self.send_uart(f"T:{len(phases)}")

        print(f"Sent {len(phases)} phase values")

    def create_control_sidebar(self):
        """Create the control sidebar"""
        # Title
        title_label = tk.Label(self.sidebar, text="CONTROLS", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 20))

        # One Shot button
        self.one_shot_btn = tk.Button(self.sidebar, text="ONE SHOT",
                                     command=self.send_one_shot,
                                     bg="#4CAF50", fg="white",
                                     font=("Arial", 10, "bold"),
                                     height=2, width=20)
        self.one_shot_btn.pack(pady=(0, 10))

        # Go to Bootloader button
        self.bootloader_btn = tk.Button(self.sidebar, text="GO TO BOOTLOADER",
                                       command=self.send_bootloader,
                                       bg="#f44336", fg="white",
                                       font=("Arial", 10, "bold"),
                                       height=2, width=20)
        self.bootloader_btn.pack(pady=(0, 20))

        # Save section
        save_frame = tk.Frame(self.sidebar)
        save_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(save_frame, text="SAVE DATA", font=("Arial", 10, "bold")).pack()

        # Save data button
        self.save_data_btn = tk.Button(save_frame, text="Save Raw Data (.json)",
                                      command=self.save_raw_data,
                                      bg="#2196F3", fg="white",
                                      height=2, width=20)
        self.save_data_btn.pack(pady=(5, 5))

        # Save chart button
        self.save_chart_btn = tk.Button(save_frame, text="Save Chart (.png)",
                                       command=self.save_chart,
                                       bg="#FF9800", fg="white",
                                       height=2, width=20)
        self.save_chart_btn.pack(pady=(5, 0))

        # Status section
        status_frame = tk.Frame(self.sidebar)
        status_frame.pack(fill=tk.X, pady=(20, 0))

        tk.Label(status_frame, text="STATUS", font=("Arial", 10, "bold")).pack()

        self.status_label = tk.Label(status_frame, text="Ready", fg="green")
        self.status_label.pack(pady=(5, 0))

        # Data info
        self.data_info_label = tk.Label(status_frame, text="No data received", fg="gray")
        self.data_info_label.pack(pady=(5, 0))

    def send_uart(self, command: str):
        if ser and ser.is_open:
            msg = f"<{command}>\n"
            print("Sending:", msg.strip())
            ser.write(msg.encode())
            self.update_status("Command sent")

    def send_one_shot(self):
        self.update_status("Triggering one shot...")
        self.send_uart("S")

    def send_bootloader(self):
        result = messagebox.askyesno("Confirm", "Are you sure you want to go to bootloader?")
        if result:
            self.send_uart("B")

    def save_raw_data(self):
        """Save raw data as JSON file"""
        if not self.current_data:
            messagebox.showwarning("Warning", "No data to save")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"{self.experiment_title.get()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        if filename:
            try:
                data_to_save = {
                    "experiment_title": self.experiment_title.get(),
                    "experiment_name": self.experiment_var.get(),
                    "timestamp": datetime.now().isoformat(),
                    "data": self.current_data,
                    "data_length": len(self.current_data)
                }

                with open(filename, 'w') as f:
                    json.dump(data_to_save, f, indent=2)

                messagebox.showinfo("Success", f"Data saved to {filename}")
                self.update_status("Data saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save data: {e}")

    def save_chart(self):
        """Save chart as PNG file"""
        if not self.current_data:
            messagebox.showwarning("Warning", "No chart data to save")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialfile=f"{self.experiment_title.get()}_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )

        if filename:
            try:
                # Update chart title with experiment info
                chart_title = f"Sonar Profile - {self.experiment_title.get()}"
                if self.experiment_var.get():
                    chart_title += f" ({self.experiment_var.get()})"

                self.ax.set_title(chart_title)
                self.fig.savefig(filename, dpi=300, bbox_inches='tight')

                messagebox.showinfo("Success", f"Chart saved to {filename}")
                self.update_status("Chart saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save chart: {e}")

    def update_status(self, message):
        """Update status label"""
        try:
            if self.running and hasattr(self, 'status_label'):
                self.status_label.config(text=message)
        except tk.TclError:
            # GUI has been destroyed, ignore the update
            pass

    def uart_reader(self):
        buffer = b""
        while self.running and ser and ser.is_open:
            try:
                # Read in chunks for better performance
                chunk = ser.read(1024)
                if not chunk:
                    continue
                buffer += chunk

                # Look for complete packets
                while PREAMBLE in buffer:
                    # Find preamble
                    index = buffer.find(PREAMBLE)

                    # Check if we have enough data for a complete packet
                    if len(buffer) >= index + PACKET_SIZE:
                        # Extract payload
                        payload = buffer[index + 2: index + 2 + PAYLOAD_SIZE]
                        buffer = buffer[index + PACKET_SIZE:]  # Remove parsed data

                        # Convert bytes to list of ints
                        data = list(payload)
                        print(f"Received packet: {len(data)} bytes")
                        print(f"First 10 values: {data[:10]}")
                        print(f"Last 10 values: {data[-10:]}")
                        self.data_queue.put(data)
                        self.update_status(f"Data received: {len(data)} points")
                    else:
                        # Incomplete packet, wait for more data
                        print(f"Waiting for more data. Buffer size: {len(buffer)}, Need: {PACKET_SIZE}")
                        break

                # Prevent buffer from growing too large
                if len(buffer) > PACKET_SIZE * 2:
                    print(f"Buffer overflow, trimming. Size was: {len(buffer)}")
                    buffer = buffer[-PACKET_SIZE:]

                # Print any leftover data that doesn't match our packet format
                if len(buffer) > 0 and PREAMBLE not in buffer:
                    leftover = buffer.decode('utf-8', errors='ignore')
                    if leftover.strip():  # Only print if there's actual content
                        print(f"Leftover UART data: {repr(leftover)}")
                    buffer = b""  # Clear the buffer since it's not our packet format

            except Exception as e:
                print("UART read error:", e)
                if self.running:
                    self.update_status("UART error")

    def update_chart(self):
        try:
            if not self.running:
                return

            while not self.data_queue.empty():
                data = self.data_queue.get_nowait()
                self.current_data = data

                # Update chart
                print(f"Updating chart with {len(data)} points")
                self.line.set_data(range(len(data)), data)
                self.ax.set_xlim(0, len(data))
                self.ax.set_ylim(0, max(255, max(data) if data else 255))

                # For large datasets, show all data but allow zooming
                if len(data) > 1000:
                    # Show all data but set a reasonable initial view
                    self.ax.set_xlim(0, len(data))
                    # You can zoom in to see details

                self.canvas.draw()
                print(f"Chart updated with xlim: {self.ax.get_xlim()}")

                # Update data info
                try:
                    if hasattr(self, 'data_info_label'):
                        self.data_info_label.config(text=f"Data points: {len(data)}")
                    self.update_status("Chart updated")

                    # Debug: Check if the line data is actually set
                    x_data, y_data = self.line.get_data()
                    print(f"Line data: x={len(x_data)}, y={len(y_data)}")

                except tk.TclError:
                    # GUI has been destroyed, ignore the update
                    pass
        except Exception as e:
            print("Chart update error:", e)

        if self.running:
            self.root.after(100, self.update_chart)

    def stop(self):
        self.running = False
        # Wait a bit for threads to finish
        time.sleep(0.1)
        if ser and ser.is_open:
            ser.close()


# === Run App ===
if __name__ == "__main__":
    root = tk.Tk()
    app = UARTApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop(), root.destroy()))
    root.mainloop()
