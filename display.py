from machine import Pin, I2C
import utime as time

try:
    import ssd1306
except ImportError:
    ssd1306 = None

class DisplayManager:
    """
    Tailored specifically for dual-color Yellow & Blue 0.96" OLED (128x64):
    - Rows 0 to 15 (16px height): Yellow Zone (Always displays Device IP)
    - Rows 16 to 63 (48px height): Blue Zone (2 targets per row, 8 chars each, with icons)
    """
    def __init__(self, sda_pin=21, scl_pin=22, width=128, height=64, addr=0x3C):
        self.width = width
        self.height = height
        self.oled = None
        self.is_available = False
        self.last_ip = "0.0.0.0"

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

    def draw_yellow_header(self, text):
        """Draws centered text in the 16px Yellow zone (Rows 0-15) on solid yellow bar."""
        if not self.is_available:
            return
        # Solid illuminated yellow header bar
        self.oled.fill_rect(0, 0, self.width, 16, 1)
        txt_len = len(text) * 8
        x = max(0, (self.width - txt_len) // 2)
        self.oled.text(text, x, 4, 0)

    def draw_yellow_ip_header(self, ip=None, is_connected=None):
        """
        Draws the bare device IP centered in the 16px Yellow zone (no 'IP:' prefix).
        If no connection, shows centered 'NO CONNECTION' on the same line.
        """
        if not self.is_available:
            return

        if ip:
            if ip == "0.0.0.0":
                is_connected = False
            else:
                self.last_ip = ip

        if is_connected is False or not self.last_ip or self.last_ip == "0.0.0.0":
            text = "NO CONNECTION"
        else:
            text = self.last_ip

        self.draw_yellow_header(text)

    # --- CUSTOM 8x8 GRAPHIC ICONS ---

    def draw_up_icon(self, x, y, color=1):
        """Draws a crisp upward arrow icon (5x7 px)."""
        self.oled.pixel(x + 2, y, color)
        self.oled.line(x + 1, y + 1, x + 3, y + 1, color)
        self.oled.line(x, y + 2, x + 4, y + 2, color)
        self.oled.line(x + 2, y + 3, x + 2, y + 6, color)

    def draw_down_icon(self, x, y, color=1):
        """Draws a crisp downward arrow icon (5x7 px)."""
        self.oled.line(x + 2, y, x + 2, y + 3, color)
        self.oled.line(x, y + 4, x + 4, y + 4, color)
        self.oled.line(x + 1, y + 5, x + 3, y + 5, color)
        self.oled.pixel(x + 2, y + 6, color)

    def draw_antenna_icon(self, x, y, color=1):
        """Draws a clean Wi-Fi antenna icon (5x7 px)."""
        self.oled.line(x, y, x + 4, y, color)
        self.oled.line(x, y, x + 2, y + 2, color)
        self.oled.line(x + 4, y, x + 2, y + 2, color)
        self.oled.line(x + 2, y + 2, x + 2, y + 6, color)

    def draw_signal_bars(self, x, y, rssi, color=1):
        """Draws 4 Wi-Fi signal strength bars."""
        bars = 4 if rssi >= -55 else (3 if rssi >= -68 else (2 if rssi >= -80 else 1))
        self.oled.line(x, y + 5, x, y + 6, color if bars >= 1 else 0)
        self.oled.line(x + 2, y + 3, x + 2, y + 6, color if bars >= 2 else 0)
        self.oled.line(x + 4, y + 1, x + 4, y + 6, color if bars >= 3 else 0)
        self.oled.line(x + 6, y, x + 6, y + 6, color if bars >= 4 else 0)

    def draw_target_slot(self, col, row_y, host, is_up, ping_ms):
        """
        Draws an 8-character slot (64px width):
        [NAME: 4 chars] [ICON: 1 char] [PING: 3 chars]
        Total = 8 chars = 64 pixels.
        col = 0: X = 0..63
        col = 1: X = 64..127
        """
        x_base = 0 if col == 0 else 64

        # 1. Clean 4-char Hostname
        clean_name = host.replace("http://", "").replace("https://", "").split("/")[0]
        # Remove common prefix like www.
        if clean_name.startswith("www."):
            clean_name = clean_name[4:]
        tag = clean_name.split(".")[0][:4].upper()
        tag = f"{tag:<4s}"

        self.oled.text(tag, x_base, row_y, 1)

        # 2. UP/DOWN Icon (drawn at x_base + 33)
        if is_up:
            self.draw_up_icon(x_base + 33, row_y)
        else:
            self.draw_down_icon(x_base + 33, row_y)

        # 3. 3-char Ping value
        if is_up:
            if ping_ms < 100:
                ping_str = f"{ping_ms:>2.0f}m"
            elif ping_ms < 1000:
                ping_str = f"{ping_ms:>3.0f}"
            else:
                ping_str = f"{ping_ms/1000:.1f}s"
        else:
            ping_str = "ERR"

        self.oled.text(ping_str, x_base + 40, row_y, 1)

    def show_boot_screen(self):
        if not self.is_available:
            return
        self.oled.fill(0)
        self.draw_yellow_header("STARTING...")
        self.oled.text("SERVER SENTINEL", 4, 22, 1)
        self.oled.text("ESP-WROOM-32", 14, 35, 1)
        self.oled.text("Starting probe...", 0, 48, 1)
        self.oled.show()

    def show_connecting(self, ssid):
        if not self.is_available:
            return
        self.oled.fill(0)
        self.draw_yellow_header("CONNECTING...")
        self.oled.text("Connecting Wi-Fi", 0, 20, 1)
        self.oled.text(f"SSID:{ssid[:11]}", 0, 33, 1)
        self.oled.text("Please wait...", 0, 48, 1)
        self.oled.show()

    def show_ap_mode(self, ssid, ip):
        if not self.is_available:
            return
        self.last_ip = ip
        self.oled.fill(0)
        # Yellow Zone: Centered bare AP IP
        self.draw_yellow_header(ip)

        # Blue Zone
        self.oled.text(f"SSID:{ssid[:11]}", 0, 20, 1)
        self.oled.text("Connect & Open:", 0, 33, 1)
        self.oled.text(f"http://{ip}/", 0, 48, 1)
        self.oled.show()

    def show_testing(self, stage="Checking...", progress_pct=0):
        if not self.is_available:
            return
        # Preserve yellow header
        self.oled.fill_rect(0, 16, self.width, 48, 0)
        self.draw_yellow_ip_header()

        self.oled.text("PROBING TARGETS:", 0, 20, 1)
        self.oled.text(stage[:16], 0, 33, 1)

        self.oled.rect(0, 47, 128, 13, 1)
        if progress_pct > 0:
            w = max(2, int((124 * progress_pct) / 100))
            self.oled.fill_rect(2, 49, w, 9, 1)
        else:
            self.oled.text("Measuring...", 18, 50, 1)
        self.oled.show()

    def show_multi_server_status(self, servers, net_ms=0, rssi=-50, ip="", is_connected=None):
        """
        Renders the enhanced UI:
        - Yellow Header: Bare IP or centered NO CONNECTION warning
        - Rows 1 to 3 (Y=18, Y=29, Y=40): 2 targets per line (8 chars each: NAME▲PING)
        - Row 4 (Y=52): Wi-Fi Antenna Icon, RSSI dBm, Signal Bars, and Gateway Ping
        """
        if not self.is_available:
            return

        self.oled.fill(0)

        # 1. Yellow Header: Bare Device IP (centered) or NO CONNECTION
        self.draw_yellow_ip_header(ip, is_connected=is_connected)

        # 2. Render actual configured targets across Rows 1, 2, 3 (up to 6 targets, 2 per row)
        # If no website is configured or slots are empty, keep them clean and empty.
        targets = list(servers) if servers else []
        row_ys = [18, 29, 40]
        slot_idx = 0
        for s in targets[:6]:
            row = slot_idx // 2
            col = slot_idx % 2
            if row < len(row_ys):
                self.draw_target_slot(
                    col=col,
                    row_y=row_ys[row],
                    host=s.get("server", "Srv"),
                    is_up=s.get("is_up", False),
                    ping_ms=s.get("ping_ms", 0)
                )
            slot_idx += 1

        # 3. Row 4 (Y = 52): Wi-Fi Antenna Icon, RSSI dBm, Signal Bars, and Gateway Ping
        self.oled.hline(0, 50, self.width, 1)

        # Antenna icon
        self.draw_antenna_icon(0, 53)

        # RSSI text (e.g. -54dB)
        rssi_str = f"{rssi}dB"
        self.oled.text(rssi_str, 8, 54, 1)

        # Signal 4-bar indicator
        self.draw_signal_bars(54, 53, rssi)

        # Gateway ping with UP arrow: [GW][▲][38m]
        self.oled.text("GW", 68, 54, 1)
        if net_ms > 0:
            self.draw_up_icon(86, 54)
            self.oled.text(f"{net_ms:.0f}m", 94, 54, 1)
        else:
            self.draw_down_icon(86, 54)
            self.oled.text("ERR", 94, 54, 1)

        self.oled.show()

    def show_server_status(self, target="caydas.cloud", is_up=True, status_code=200, ping_ms=0, net_ms=0, rssi=-50, ip="", is_connected=None):
        """Backwards compatibility wrapper delegating to multi-server layout."""
        servers = [{
            "server": target,
            "is_up": is_up,
            "status_code": status_code,
            "ping_ms": ping_ms
        }]
        self.show_multi_server_status(servers, net_ms=net_ms, rssi=rssi, ip=ip, is_connected=is_connected)
