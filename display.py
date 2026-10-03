from machine import Pin, I2C
import utime as time

try:
    import ssd1306
except ImportError:
    ssd1306 = None

class DisplayManager:
    """
    Tailored specifically for dual-color Yellow & Blue 0.96" OLED (128x64):
    - Rows 0 to 15 (16px height): Yellow Zone (dedicated Header/Status Bar)
    - Rows 16 to 63 (48px height): Blue Zone (dedicated Metrics & Diagnostics)
    """
    def __init__(self, sda_pin=21, scl_pin=22, width=128, height=64, addr=0x3C):
        self.width = width
        self.height = height
        self.oled = None
        self.is_available = False

        if not ssd1306:
            print("SSD1306 driver module missing.")
            return

        try:
            self.i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=400000)
            devices = self.i2c.scan()
            if addr in devices:
                self.oled = ssd1306.SSD1306_I2C(self.width, self.height, self.i2c, addr=addr)
                self.is_available = True
                print(f"Dual-color OLED initialized at 0x{addr:02X} (SDA={sda_pin}, SCL={scl_pin})")
                self.show_boot_screen()
            else:
                print(f"OLED not detected at 0x{addr:02X}. Devices: {[hex(d) for d in devices]}")
        except Exception as e:
            print("Display init error:", e)

    def draw_yellow_header(self, text, inverted=True):
        """Draws exactly within the 16px Yellow zone (Rows 0-15)."""
        if not self.is_available:
            return
        if inverted:
            # Solid illuminated yellow header bar with dark text
            self.oled.fill_rect(0, 0, self.width, 16, 1)
            txt_len = len(text) * 8
            x = max(2, (self.width - txt_len) // 2)
            self.oled.text(text, x, 4, 0)
        else:
            # Yellow text with a clean horizontal divider at row 15
            self.oled.fill_rect(0, 0, self.width, 16, 0)
            txt_len = len(text) * 8
            x = max(2, (self.width - txt_len) // 2)
            self.oled.text(text, x, 4, 1)
            self.oled.hline(0, 15, self.width, 1)

    def show_boot_screen(self):
        if not self.is_available:
            return
        self.oled.fill(0)
        # Yellow Zone (0-15)
        self.draw_yellow_header("ESP32 SPEEDTEST", inverted=True)

        # Blue Zone (16-63)
        self.oled.text("Dual-Core 240MHz", 0, 20, 1)
        self.oled.text("Wi-Fi Diagnostic", 0, 33, 1)
        self.oled.text("Starting up...", 0, 48, 1)
        self.oled.show()

    def show_connecting(self, ssid):
        if not self.is_available:
            return
        self.oled.fill(0)
        # Yellow Zone
        self.draw_yellow_header("WIFI CONNECTING", inverted=True)

        # Blue Zone
        self.oled.text("Target Network:", 0, 20, 1)
        self.oled.text(ssid[:16], 0, 33, 1)
        self.oled.text("Please wait...", 0, 48, 1)
        self.oled.show()

    def show_ap_mode(self, ssid, ip):
        if not self.is_available:
            return
        self.oled.fill(0)
        # Yellow Zone
        self.draw_yellow_header("SETUP PORTAL AP", inverted=True)

        # Blue Zone
        self.oled.text(f"SSID: {ssid[:10]}", 0, 20, 1)
        self.oled.text("Connect & Open:", 0, 33, 1)
        self.oled.text(f"http://{ip}/", 0, 48, 1)
        self.oled.show()

    def show_testing(self, stage="Speed Test", progress_pct=0):
        if not self.is_available:
            return
        self.oled.fill(0)
        # Yellow Zone
        self.draw_yellow_header("RUNNING TEST", inverted=True)

        # Blue Zone
        self.oled.text("Stage:", 0, 20, 1)
        self.oled.text(stage[:16], 0, 33, 1)
        
        # Activity frame in blue zone
        self.oled.rect(0, 47, 128, 13, 1)
        if progress_pct > 0:
            w = max(2, int((124 * progress_pct) / 100))
            self.oled.fill_rect(2, 49, w, 9, 1)
        else:
            self.oled.text("Measuring...", 18, 50, 1)
        self.oled.show()

    def show_results(self, down_mbps, up_mbps, ping_ms, ip="", rssi=-50):
        if not self.is_available:
            return
        self.oled.fill(0)
        # Yellow Zone: Device IP Address
        header = f"IP {ip}" if ip else "ESP32 SPEEDTEST"
        self.draw_yellow_header(header, inverted=True)

        # Blue Zone (Rows 16 to 63): 4 clear diagnostic rows
        # Row 1: Download Speed
        self.oled.text("DOWN:", 0, 20, 1)
        self.oled.text(f"{down_mbps:.2f} Mbps", 44, 20, 1)

        # Row 2: Upload Speed
        self.oled.text("UP:  ", 0, 31, 1)
        self.oled.text(f"{up_mbps:.2f} Mbps", 44, 31, 1)

        # Row 3: Latency (Ping)
        self.oled.text("PING:", 0, 42, 1)
        self.oled.text(f"{ping_ms:.0f} ms", 44, 42, 1)

        # Row 4: Wi-Fi Signal Strength
        self.oled.text("WIFI:", 0, 53, 1)
        pct = 100 if rssi >= -50 else (85 if rssi >= -60 else (70 if rssi >= -70 else 50))
        self.oled.text(f"{rssi}dBm [{pct}%]", 44, 53, 1)

        self.oled.show()

    def show_server_status(self, target="caydas.cloud", is_up=True, status_code=200, ping_ms=0, net_ms=0, rssi=-50, ip=""):
        if not self.is_available:
            return
        self.oled.fill(0)
        # Yellow Zone (Rows 0-15): Server Name and UP/DOWN status
        status_txt = "ONLINE" if is_up else "OFFLINE"
        short_name = target.replace("http://", "").replace("https://", "").split("/")[0]
        hdr = f"{short_name[:8]}: {status_txt}"
        self.draw_yellow_header(hdr, inverted=is_up)

        # Blue Zone (Rows 16-63)
        # Row 1: State & Status code
        code_txt = f"{status_code}" if status_code > 0 else "ERR"
        self.oled.text(f"STATUS: {status_txt} ({code_txt})", 0, 20, 1)

        # Row 2: Latency to server
        self.oled.text(f"SRV PING: {ping_ms:.0f} ms", 0, 31, 1)

        # Row 3: Internet gateway latency (1.1.1.1)
        gate_txt = f"{net_ms:.0f} ms" if net_ms > 0 else "DOWN"
        self.oled.text(f"GATEWAY:  {gate_txt}", 0, 42, 1)

        # Row 4: Wi-Fi Signal
        pct = 100 if rssi >= -50 else (85 if rssi >= -60 else (70 if rssi >= -70 else 50))
        self.oled.text(f"WIFI: {rssi}dBm [{pct}%]", 0, 53, 1)

        self.oled.show()

