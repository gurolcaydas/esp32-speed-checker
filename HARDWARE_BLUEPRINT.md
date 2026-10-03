# 🛠️ AI HARDWARE BLUEPRINT & SPECIFICATION GUIDE
> **Target Audience:** Future AI coding assistants (and developers) working on this specific ESP32 hardware setup.
> **Purpose:** Eliminate discovery overhead, avoid reinventing drivers, and prevent known MicroPython pitfalls, memory crashes, and hardware limits in advance.

---

## 1. 📋 Hardware Overview & Specifications

| Component | Specification | Notes / Constraints |
| :--- | :--- | :--- |
| **Microcontroller** | **ESP-WROOM-32** (ESP32-D0WDQ6) | Xtensa dual-core 32-bit LX6 up to 240 MHz |
| **Flash Memory** | **4 MB SPI Flash** | Formatted as FAT / LittleFS by MicroPython |
| **SRAM / Heap** | **520 KB SRAM** (~300 KB usable) | **Heap limit ~100–150 KB free**. Large contiguous allocations will crash! |
| **Wi-Fi** | **2.4 GHz 802.11 b/g/n (1x1 SISO)** | WPA/WPA2 Personal. *No 5 GHz support*. |
| **Onboard LED** | **GPIO 2** (active HIGH) | Useful for connection status and blink indicators |
| **USB-UART Port** | **COM4** (115200 baud, 8-N-1) | Standard CP2102 / CH340 USB-to-UART bridge |
| **Firmware** | **MicroPython v1.29.0** (Generic ESP32 build) | Binary: `ESP32_GENERIC-20260824-v1.29.0.bin` |

---

## 2. 📺 Display & I2C Pinout

The board is wired to a **0.96" Dual-Color OLED Display (128x64 pixels)** using the SSD1306 controller.

### Hardware Pin Mapping:
* **SDA:** `GPIO 21`
* **SCL:** `GPIO 22`
* **I2C Bus:** `I2C(0)`
* **I2C Address:** `0x3C` (confirmed via `i2c.scan()`)
* **Clock Speed:** `400,000 Hz` (Fast-mode I2C)

### ⚠️ Physical Dual-Color Zone Split (CRITICAL FOR UI DESIGN):
This OLED is **physically divided into two distinct color zones**:
1. **Yellow Zone (Rows 0 to 15, 16px high):**
   * Top 16 pixels glow bright Yellow.
   * **Rule:** Always use this area for a title bar, target name, or status pill (`ONLINE`/`OFFLINE`). Invert it (`fill_rect(0, 0, 128, 16, 1)`) for solid contrast alert headers.
2. **Blue Zone (Rows 16 to 63, 48px high):**
   * Lower 48 pixels glow bright Blue.
   * **Rule:** Use rows 16–63 for diagnostic data, charts, metrics, or server lists. Typically fits **4 lines of 8x8 text** (e.g. Y = 20, 31, 42, 53).

### Tested Driver:
* **[ssd1306.py](file:///c:/Users/gcayd/OneDrive/Desktop/code/esp32/ssd1306.py)** (MicroPython `framebuf` driver).
* High-level manager: **[display.py](file:///c:/Users/gcayd/OneDrive/Desktop/code/esp32/display.py)** (`DisplayManager`).

---

## 3. 🚨 CRITICAL LESSONS LEARNED & PITFALLS (AVOID THESE!)

### ❌ PITFALL 1: Large String Constants in Python Code (`MemoryError`)
* **What Happened:** Embedding a 30 KB HTML/CSS/JS template string directly in a `.py` file caused:
  ```text
  MemoryError: memory allocation failed, allocating 30681 bytes
  ```
  MicroPython requires *contiguous* RAM blocks. Even if total free RAM is 80 KB, a single 30 KB allocation will fail due to memory fragmentation!
* **Golden Rule for Next AI:**
  * **NEVER store large HTML/CSS/JS templates as Python string variables.**
  * Save the UI as a standalone file (e.g., `index.html`) on flash.
  * Stream the file to the client socket in **1024-byte (1 KB) chunks**:
    ```python
    def send_file(cl, filepath, content_type="text/html"):
        cl.send(f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nConnection: close\r\n\r\n".encode('utf-8'))
        with open(filepath, 'rb') as f:
            buf = bytearray(1024)
            while True:
                n = f.readinto(buf)
                if not n:
                    break
                cl.sendall(buf[:n])
    ```
  * Memory overhead drops from 30+ KB to **1 KB**!

---

### ❌ PITFALL 2: Expecting Broadband Download Speeds (1.26 Mbps vs 60 Mbps)
* **What Happened:** Running a broadband speedtest on ESP32 measured ~1.26 Mbps while a PC on the same Wi-Fi achieved 60 Mbps.
* **Why:** 
  * MicroPython lwIP uses a tiny TCP receive window (`TCP_WND` = ~4 KB).
  * Maximum single-stream TCP throughput is capped by Bandwidth-Delay Product:
    $$\text{Max Throughput} \approx \frac{\text{Window Size (32,768 bits)}}{\text{RTT (0.030s)}} \approx 1.09\text{ Mbps}$$
* **Golden Rule for Next AI:**
  * Do **not** use the ESP32 for high-throughput broadband speed benchmarking.
  * **Use it for what it excels at:** Latency / Ping tracking, HTTP health checks, Uptime Sentinels (Heartbeats), REST APIs, sensor logging, and hardware control.

---

### ❌ PITFALL 3: Date & Year Reverting to 2000
* **What Happened:** MicroPython RTC resets to `2000-01-01` on every boot.
* **Golden Rule for Next AI:**
  * Always synchronize time with NTP once Wi-Fi connects:
    ```python
    import ntptime
    ntptime.host = "pool.ntp.org"
    ntptime.settime() # Sets RTC to UTC
    ```
  * User's local timezone is **UTC+3 (Turkey Time)**:
    ```python
    local_time = time.localtime(time.time() + (3 * 3600))
    ```

---

### ❌ PITFALL 4: Leaking Credentials on GitHub
* **What Happened:** `config.json` contained actual home Wi-Fi credentials (`"yogaincappadocia"` / `"ozanezgi"`).
* **Golden Rule for Next AI:**
  * Ensure `.gitignore` **always** ignores:
    ```gitignore
    config.json
    stats.json
    history.json
    secrets.py
    *.bin
    ```
  * Keep `config.example.json` with dummy values for repository clones.

---

## 4. 🚀 Flashing, Deployment & Tooling

### Uploading Files over USB (Without 3rd-Party Tools):
Use the included **[sync_esp.py](file:///c:/Users/gcayd/OneDrive/Desktop/code/esp32/sync_esp.py)** script. It talks directly to the MicroPython Raw REPL over `COM4` at `115200` baud:

```bash
# Upload all project files & soft-reboot ESP32
python sync_esp.py

# Upload with new Wi-Fi credentials
python sync_esp.py "SSID" "PASSWORD"
```

### Viewing Live Device Logs:
```bash
python serial_monitor.py
```

### Automated GitHub Publishing:
GitHub CLI (`gh`) is installed and authenticated for user **`gurolcaydas`**.
```bash
# Publish any new project folder automatically
python publish_to_github.py
```

---

## 5. 🏗️ Recommended Architecture for Future Projects

```
esp32-project/
├── config.json          # Ignored by git; live device configuration
├── config.example.json  # Git-committed template configuration
├── config_manager.py    # Safe JSON load/save with default fallbacks
├── ssd1306.py           # OLED display hardware driver
├── display.py           # DisplayManager handling 16px Yellow & 48px Blue zones
├── index.html           # Standalone web UI (streamed in 1KB chunks!)
├── webserver.py         # Lightweight non-blocking HTTP socket server
├── main.py              # Boot entry point, Wi-Fi fallback AP, main loop
├── sync_esp.py          # PC deployment script over COM4
└── publish_to_github.py # 1-click GitHub creator & publisher
```

### Main Loop Template (Non-Blocking):
Always keep web server sockets non-blocking (`server_socket.settimeout(0.2)`) and yield via `time.sleep_ms(20)` so background tasks, buttons, sensors, and OLED rendering run smoothly together:

```python
while True:
    server.handle_client()      # Checks for HTTP requests (non-blocking)
    handle_periodic_tasks()     # Sensor reads / uptime checks
    gc.collect()                # Keep heap clean
    time.sleep_ms(20)
```
