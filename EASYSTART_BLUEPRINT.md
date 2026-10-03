# 🚀 ESP32 + 0.96" Dual-Color OLED EasyStart Blueprint
> **Standalone Hardware Specification, Driver & Quickstart Guide**  
> *Self-contained reference for starting new projects on this hardware setup on any computer.*  
> *No dependencies on local repository files.*

---

## 1. 📋 Hardware Overview & Specifications

| Component | Specification | Practical Notes & Limits |
| :--- | :--- | :--- |
| **Microcontroller** | **ESP-WROOM-32** (ESP32-D0WDQ6) | Dual-core Tensilica Xtensa 32-bit LX6 up to 240 MHz |
| **Flash Memory** | **4 MB SPI Flash** | Managed as LittleFS / FAT by MicroPython (~2 MB usable user disk) |
| **SRAM / Heap** | **520 KB SRAM** (~300 KB usable) | **Usable free heap is ~100–140 KB**. Large contiguous allocations crash with `MemoryError`! |
| **Wi-Fi** | **2.4 GHz 802.11 b/g/n (1x1 SISO)** | WPA / WPA2 Personal supported. **No 5 GHz Wi-Fi**. |
| **Onboard LED** | **GPIO 2** (Active HIGH) | Blue LED on most DevKit boards. Pulls HIGH during boot. |
| **Display** | **0.96" OLED (128x64)** | SSD1306 Controller, I2C interface, Dual-Color (Yellow/Blue). |
| **I2C Address** | **`0x3C`** (Default) | Verified via I2C scanner at 400 kHz clock speed. |
| **Serial / Baud** | **115200 baud, 8-N-1** | CP2102 / CH340 USB-UART bridge. |

---

## 2. 🔌 Physical Wiring & Pinout

### OLED Display to ESP32 Pin Mapping:
| OLED Pin | ESP32 Pin | Function |
| :--- | :--- | :--- |
| **GND** | **GND** | Ground |
| **VCC** | **3V3** (or 5V) | 3.3V Power Supply |
| **SCL** | **GPIO 22** | I2C Clock (`I2C(0)`) |
| **SDA** | **GPIO 21** | I2C Data (`I2C(0)`) |

### ESP32 GPIO Usage Guide for Future Sensors & Peripherals:
* **Safe General Purpose I/O (Use freely):**  
  `GPIO 4`, `GPIO 16`, `GPIO 17`, `GPIO 18`, `GPIO 19`, `GPIO 23`, `GPIO 25`, `GPIO 26`, `GPIO 27`, `GPIO 32`, `GPIO 33`.
* **Input-Only Pins (No internal pullups/pulldowns, cannot drive outputs):**  
  `GPIO 34`, `GPIO 35`, `GPIO 36 (VP)`, `GPIO 39 (VN)`.  
  *Ideal for ADC analog sensors (photoresistors, thermistors, analog potentiometers).*
* **Boot Strapping Pins (Exercise caution):**  
  * `GPIO 0`: Connected to BOOT button. Must be HIGH during normal boot.
  * `GPIO 2`: Connected to onboard blue LED. Must be LOW or floating during flashing.
  * `GPIO 12`, `GPIO 15`: JTAG / voltage selection pins. Avoid driving at boot.
* **Flash Pins (NEVER USE):**  
  `GPIO 6`, `GPIO 7`, `GPIO 8`, `GPIO 9`, `GPIO 10`, `GPIO 11` are hardwired to the onboard SPI Flash. Accessing them will crash the ESP32.

---

## 3. 📺 OLED Physical Split & UI Layout

The 0.96" OLED is **physically manufactured with two distinct color bands**:
```
+-------------------------------------------------------+
|  ROWS 0 - 15  (16px height)  -  BRIGHT YELLOW ZONE    |
|  [Centered Bare IP / Status Banner: 16 chars max]    |
+-------------------------------------------------------+  <-- Physical gap
|  ROWS 16 - 63 (48px height)  -  BRIGHT BLUE ZONE      |
|  Row 1 (Y=18): [Slot 0: 8 chars] [Slot 1: 8 chars]    |
|  Row 2 (Y=29): [Slot 2: 8 chars] [Slot 3: 8 chars]    |
|  Row 3 (Y=40): [Slot 4: 8 chars] [Slot 5: 8 chars]    |
|  Row 4 (Y=52): [Wi-Fi Icon, RSSI, Bars, Gateway Ping]  |
+-------------------------------------------------------+
```

### Display Grid Math:
* **Resolution:** 128 wide $\times$ 64 high.
* **Standard Font:** MicroPython default font is $8\times 8$ pixels per character.
* **Horizontal Capacity:** Exactly $\frac{128}{8} = 16\text{ characters}$ per line.
* **Yellow Zone (Y=0..15):** Fits 1 or 2 text lines (vertically centered at $Y=4$ for single line).
  * Design rule: Invert bar (`fill_rect(0, 0, 128, 16, 1)`) with black text (`color=0`) for maximum visual contrast.
  * Center text formula: `x = (128 - len(text) * 8) // 2`.
* **Blue Zone (Y=16..63):** 48 pixels high. Fits up to 4 clean lines ($Y=18, 29, 40, 52$).

---

## 4. ⚡ Step-by-Step Initial Setup (From Scratch)

### Step 1: Install Python Tools on PC
Open terminal or command prompt:
```bash
pip install esptool pyserial
```

### Step 2: Download MicroPython Firmware
Download the latest stable generic ESP32 firmware binary (`.bin`) from:
👉 **https://micropython.org/download/ESP32_GENERIC/**

### Step 3: Flash MicroPython to ESP32
Connect the board via USB (replace `COM4` with your USB port, e.g. `/dev/ttyUSB0` on Linux/Mac):
```bash
# 1. Erase old flash
esptool.py --chip esp32 --port COM4 erase_flash

# 2. Flash MicroPython at offset 0x1000
esptool.py --chip esp32 --port COM4 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC-*.bin
```

---

## 5. 📦 Embedded MicroPython SSD1306 Driver

Save this complete, self-contained driver as **`ssd1306.py`** on the ESP32:

```python
# MicroPython SSD1306 OLED driver, I2C and SPI interfaces
import time
import framebuf

SET_CONTRAST = 0x81
SET_ENTIRE_ON = 0xA4
SET_NORM_INV = 0xA6
SET_DISP = 0xAE
SET_MEM_ADDR = 0x20
SET_COL_ADDR = 0x21
SET_PAGE_ADDR = 0x22
SET_DISP_START_LINE = 0x40
SET_SEG_REMAP = 0xA0
SET_MUX_RATIO = 0xA8
SET_COM_OUT_DIR = 0xC0
SET_DISP_OFFSET = 0xD3
SET_COM_PIN_CFG = 0xDA
SET_DISP_CLK_DIV = 0xD5
SET_PRECHARGE = 0xD9
SET_VCOM_DESEL = 0xDB
SET_CHARGE_PUMP = 0x8D

class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,
            SET_MEM_ADDR, 0x00,
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,
            SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08,
            SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x02 if self.height == 32 else 0x12,
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL, 0x30,
            SET_CONTRAST, 0xFF,
            SET_ENTIRE_ON,
            SET_NORM_INV,
            SET_CHARGE_PUMP, 0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01,
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)

class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)
```

---

## 6. 🛠️ Ready-to-Run Starter Boilerplates

### A. Minimal OLED Test (`main.py`):
```python
from machine import Pin, I2C
import ssd1306
import time

# Initialize Fast I2C on GPIO 21/22
i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

# 1. Clear screen
oled.fill(0)

# 2. Yellow Zone: Solid inverted header bar with centered text
oled.fill_rect(0, 0, 128, 16, 1)
title = "SYSTEM READY"
x_pos = (128 - len(title) * 8) // 2
oled.text(title, x_pos, 4, 0) # Black text on yellow background

# 3. Blue Zone: Text & Lines
oled.text("ESP-WROOM-32", 0, 22, 1)
oled.text("OLED 128x64 OK", 0, 36, 1)
oled.hline(0, 50, 128, 1)
oled.text("Waiting tasks...", 0, 54, 1)

oled.show()
print("OLED test successfully rendered!")
```

### B. Safe Wi-Fi Connector with LED & Fallback AP:
```python
import network
import time
from machine import Pin

led = Pin(2, Pin.OUT)

def connect_wifi(ssid, password, timeout_s=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        led.value(1)
        return wlan.ifconfig()[0]

    print(f"Connecting to Wi-Fi '{ssid}'...")
    wlan.connect(ssid, password)
    start = time.time()
    
    while not wlan.isconnected() and (time.time() - start) < timeout_s:
        led.value(not led.value()) # Blink while connecting
        time.sleep_ms(300)

    if wlan.isconnected():
        led.value(1) # Solid ON when connected
        ip = wlan.ifconfig()[0]
        print(f"Wi-Fi Connected! IP: {ip}")
        return ip
    else:
        led.value(0)
        print("Wi-Fi failed. Launching Access Point...")
        return start_ap()

def start_ap(ap_ssid="ESP32-Setup", ap_pass=""):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ap_ssid, authmode=network.AUTH_OPEN if not ap_pass else network.AUTH_WPA_WPA2_PSK, password=ap_pass)
    ip = ap.ifconfig()[0]
    print(f"AP Active: SSID={ap_ssid}, IP={ip}")
    return ip
```

### C. Safe Web Server (1KB Chunked File Streaming - Avoids MemoryError!):
```python
import usocket as socket
import gc

def send_file(client_socket, filepath, content_type="text/html"):
    """Streams a file in 1KB chunks. Uses only 1KB RAM instead of 30KB!"""
    client_socket.send(f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nConnection: close\r\n\r\n".encode('utf-8'))
    with open(filepath, 'rb') as f:
        buf = bytearray(1024)
        while True:
            n = f.readinto(buf)
            if not n:
                break
            client_socket.sendall(buf[:n])

def run_webserver(port=80):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', port))
    server.listen(2)
    server.settimeout(0.2) # Non-blocking accept
    print(f"Server listening on port {port}")

    while True:
        try:
            cl, addr = server.accept()
            req = cl.recv(1024)
            # Route request
            send_file(cl, "index.html")
            cl.close()
        except OSError:
            pass # Timeout with no incoming client; yield to background loop
        gc.collect()
        time.sleep_ms(20)
```

### D. Time Synchronization (NTP + Local Timezone):
```python
import ntptime
import time

def sync_time(utc_offset_hours=3):
    """Syncs RTC with pool.ntp.org and returns local time tuple."""
    try:
        ntptime.host = "pool.ntp.org"
        ntptime.settime() # Sets hardware RTC to UTC
        print("NTP sync successful.")
    except Exception as e:
        print("NTP sync skipped:", e)
    
    # Returns (year, month, mday, hour, minute, second, weekday, yearday)
    return time.localtime(time.time() + (utc_offset_hours * 3600))
```

---

## 7. 🚨 Top 7 Golden Rules (Hardware Gotchas to Avoid)

1. **NEVER store HTML/JS templates in Python string variables:**
   MicroPython requires contiguous heap blocks. A 30 KB string variable causes `MemoryError: memory allocation failed`. Always save the UI as a standalone `index.html` on flash and stream in 1024-byte chunks.
2. **Do NOT use ESP32 for broadband speed testing:**
   MicroPython lwIP TCP receive window is tiny (~4 KB). Maximum single-stream TCP throughput is capped at ~1.2 Mbps by the Bandwidth-Delay Product. Use the ESP32 for latency, uptime, HTTP APIs, and sensor control.
3. **Cap History / Log Files at 20 Entries:**
   Unbounded arrays in RAM or frequent JSON file writes will exhaust heap and wear out flash memory. Always use a sliding window (`if len(history) > 20: history.pop(0)`) and run `gc.collect()` before/after JSON operations.
4. **Beware of Falsy Empty Lists in Python:**
   `targets = user_list or [default]` evaluates to `[default]` when `user_list == []`! If a user deletes all items, an empty list must be preserved using `targets = user_list if user_list is not None else [default]`.
5. **Always sync time via NTP:**
   The ESP32 RTC resets to `2000-01-01` on every boot. Sync with NTP immediately after Wi-Fi connects.
6. **Preserve Device Configuration during PC Syncs:**
   Before uploading a default `config.json` from a PC, check if `config.json` already exists on the ESP32. Don't overwrite settings configured by the user via the device's web portal.
7. **Always ignore `config.json` in git:**
   Never commit home Wi-Fi credentials or passwords to GitHub. Use `config.example.json` with dummy values for repository templates.

---

## 8. 💻 Universal PC Deployment Tool (`upload.py`)

Save this standalone 45-line Python script on your PC. It uploads files over USB to the ESP32 using the built-in MicroPython Raw REPL without installing third-party IDEs:

```python
import serial, time, os, sys

PORT = sys.argv[1] if len(sys.argv) > 1 else 'COM4'
BAUD = 115200

def raw_repl_exec(ser, cmd):
    ser.write(cmd.encode('utf-8') + b'\x04')
    return ser.read_until(b'\x04>')

def upload(port, filepath):
    ser = serial.Serial(port, BAUD, timeout=2)
    ser.write(b'\r\x03\x03\r\x01') # Interrupt and enter Raw REPL
    time.sleep(0.4)
    ser.read_all()

    filename = os.path.basename(filepath)
    print(f"Uploading {filepath} -> {filename}...")
    with open(filepath, 'rb') as f:
        data = f.read()

    raw_repl_exec(ser, f"f = open('{filename}', 'wb')\n")
    for i in range(0, len(data), 512):
        chunk = repr(data[i:i+512])
        raw_repl_exec(ser, f"f.write({chunk})\n")
    raw_repl_exec(ser, "f.close()\n")
    print(f"Done ({len(data)} bytes). Rebooting ESP32...")

    ser.write(b'\x02\x04') # Exit raw REPL and soft reboot (Ctrl+D)
    time.sleep(0.5)
    print(ser.read(1024).decode('utf-8', errors='replace'))
    ser.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python upload.py <COM_PORT> <FILE_PATH>")
    else:
        upload(sys.argv[1], sys.argv[2])
```

*(Alternatively, you can install the official tool: `pip install mpremote` and run `mpremote cp main.py :main.py`)*
