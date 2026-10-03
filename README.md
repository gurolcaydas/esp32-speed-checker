# ESP32 Server Sentinel & Latency Monitor

A dedicated hardware sentinel station built on the **ESP-WROOM-32** with an onboard Web Server and 0.96" Dual-Color OLED display, designed to continuously monitor **`caydas.cloud`** server uptime, HTTP response health, network latency, and Wi-Fi quality 24/7.

---

## 🎯 What It Does

* **`my-server-up` Flag:** Probes `caydas.cloud` on port 80/HTTP to immediately detect server outages, response codes (`HTTP 200 OK`), and connection timeouts.
* **Millisecond Precision Latency:** Measures TCP handshake and TTFB (Time to First Byte) latency to `caydas.cloud` and jitter.
* **Internet vs. Server Disambiguation:** Simultaneously pings global internet gateway (`1.1.1.1`) to clearly distinguish whether an outage is caused by your local Wi-Fi / ISP or `caydas.cloud` itself.
* **Automated Heartbeat & Scheduling:** Runs periodic background health checks (default: every 5 minutes; configurable to 1m, 2m, 5m, 15m, 30m, 1h, or manual-only).
* **Interactive Latency Trend Chart:** Responsive HTML5 Canvas chart displaying latency curves over time with hover crosshair tooltips.
* **Daily & Monthly Uptime & Extremes:** Tracks Uptime % (e.g. 100.0%) and the **Lowest** (peak performance) and **Highest** (latency spike) response times for **Today** and **This Month**.
* **Dual-Color OLED Display (128x64):**
  * **Yellow Zone:** Prominent inverted status bar (`CAYDAS.C: ONLINE` or `OFFLINE`).
  * **Blue Zone:** Live Server status & HTTP code, server ping (ms), internet gateway ping (ms), and Wi-Fi signal (dBm).

---

## 🚀 How to Connect & View

1. Connect to the dashboard at:
   ```
   http://<esp32-ip>/
   ```
   *(Or if in setup AP mode: connect to Wi-Fi `ESP32-ServerMonitor` and open `http://192.168.4.1/`)*
2. View real-time status, trigger on-demand probes with **"Check Server Now"**, adjust check intervals, or change the target server.

---

## 💻 Deploy to ESP32

To push the latest code to your ESP32 over USB (COM4):
```bash
python sync_esp.py
```

To watch live console logs:
```bash
python serial_monitor.py
```

---

## 🛠️ Hardware Blueprint & AI Context
For pinouts, physical OLED color zone splits, MicroPython memory best practices, and lessons learned for future projects, see:
👉 **[HARDWARE_BLUEPRINT.md](file:///c:/Users/gcayd/OneDrive/Desktop/code/esp32/HARDWARE_BLUEPRINT.md)**

