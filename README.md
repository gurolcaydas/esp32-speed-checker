# ESP32 Network Speed Checker

Your **ESP-WROOM-32** is now programmed as a standalone **Network Speed Checker & Diagnostic Station** with an onboard Web Server and interactive dashboard.

---

## 🚀 How to Connect & Use

### Method 1: Connect via Setup Wi-Fi (Phone or PC)
1. On your phone or laptop, look for the Wi-Fi network:
   * **SSID:** `ESP32-SpeedChecker`
   * *(Open network / no password)*
2. Once connected, open your browser and navigate to:
   * **URL:** [http://192.168.4.1](http://192.168.4.1)
3. Under **Wi-Fi Settings**, enter your home Wi-Fi name (SSID) and Password, then click **Save & Reconnect**.
4. The ESP32 will connect to your home Wi-Fi, obtain its local IP address (e.g., `192.168.1.150`), and serve the dashboard directly on your local network!

---

### Method 2: Configure Directly from PC
You can also set your Wi-Fi credentials directly over USB without using the setup Access Point:
```bash
python sync_esp.py "YOUR_WIFI_SSID" "YOUR_WIFI_PASSWORD"
```
The script will configure the ESP32 and reboot it.

---

## 📊 Features & Diagnostics

* **Download & Upload Speed Test:** Measures real-world HTTP throughput (in Mbps) by streaming payload chunks from Cloudflare CDN speedtest endpoints.
* **Latency & Jitter:** Measures TCP socket handshake time to `1.1.1.1` to compute Minimum, Average, Maximum ping and jitter in milliseconds.
* **Wi-Fi Signal Quality (RSSI):** Reads signal strength in dBm, calculating signal percentage and connection rating (*Excellent, Good, Fair, Poor*).
* **Automated Interval Testing:**
  * Runs periodic background benchmark tests (default: every 30 minutes).
  * Interval schedule is easily configurable directly on the Web Dashboard (Disabled, 5 min, 15 min, 30 min, 1h, 2h, 6h, 12h, 24h).
  * Live status pill showing next test countdown.
* **Interactive Performance Trend Chart:**
  * Responsive Canvas chart showing historical performance curves for Download (Cyan), Upload (Purple), and Latency (Sky Blue).
  * Filter toggles (*All Metrics*, *Speed Only*, *Latency Only*).
  * Hover / touch crosshairs with precise tooltips.
* **Today & Month Extremes (Peak & Low Diagnostics):**
  * Tracks and displays the **Highest** and **Lowest** download speeds, upload speeds, and latency for **Today** and **This Month**.
  * Shows average speeds and total test counts, persisted across reboots.
* **Live Interactive Web Dashboard:**
  * Real-time metric cards with animations.
  * **"Start Speed Test"** on-demand button.
  * Recent test history table with timestamps and performance ratings.
  * Built-in Wi-Fi configuration form.
* **Serial Terminal Output:** Watch real-time test progress directly on your PC:
  ```bash
  python serial_monitor.py
  ```

---

## 📁 File Structure

* `main.py`: Device entry point; manages Wi-Fi station/AP fallback and main loop.
* `speedtest.py`: Speed test engine for latency, download, upload, and RSSI.
* `webserver.py`: Micro HTTP server hosting the dashboard and REST API (`/api/status`, `/api/run`, `/api/config`).
* `config_manager.py`: Persistent configuration storage in `config.json`.
* `sync_esp.py`: PC deployment tool to upload code and sync credentials over COM4.
* `serial_monitor.py`: Real-time serial monitor to view live logs.
