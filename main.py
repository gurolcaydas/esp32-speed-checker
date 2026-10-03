import network
import utime as time
from machine import Pin
import gc

from config_manager import ConfigManager
from speedtest import SpeedTester
from webserver import WebServer
from display import DisplayManager

# Onboard LED (usually GPIO 2 on ESP-WROOM-32)
try:
    led = Pin(2, Pin.OUT)
    led.value(0)
except Exception:
    led = None

def blink_led(times=3, delay_ms=100):
    if not led:
        return
    for _ in range(times):
        led.value(1)
        time.sleep_ms(delay_ms)
        led.value(0)
        time.sleep_ms(delay_ms)

def sync_ntp():
    try:
        import ntptime
        ntptime.host = "pool.ntp.org"
        ntptime.settime()
        print("NTP time synchronized.")
    except Exception as e:
        print("NTP sync skipped:", e)

def connect_wifi(ssid, password, disp=None, timeout_s=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        sync_ntp()
        return True, wlan.ifconfig()[0]

    print(f"Connecting to Wi-Fi '{ssid}'...")
    if disp:
        disp.show_connecting(ssid)

    wlan.connect(ssid, password)

    start = time.time()
    while not wlan.isconnected() and (time.time() - start) < timeout_s:
        if led:
            led.value(not led.value())
        time.sleep_ms(300)

    if wlan.isconnected():
        if led:
            led.value(1) # Solid ON when connected
        ip = wlan.ifconfig()[0]
        print(f"Connected successfully! ESP32 IP: {ip}")
        sync_ntp()
        return True, ip
    else:
        if led:
            led.value(0)
        print("Failed to connect to Wi-Fi within timeout.")
        return False, None

def start_access_point(ap_ssid="ESP32-SpeedChecker", ap_password="", disp=None):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    if ap_password:
        ap.config(essid=ap_ssid, password=ap_password, authmode=network.AUTH_WPA_WPA2_PSK)
    else:
        ap.config(essid=ap_ssid, authmode=network.AUTH_OPEN)
    
    ip = ap.ifconfig()[0]
    if disp:
        disp.show_ap_mode(ap_ssid, ip)
    print("\n" + "="*50)
    print("  [SETUP MODE] Wi-Fi Access Point Active")
    print(f"  SSID: {ap_ssid}")
    print(f"  Web Portal: http://{ip}/")
    print("  Connect your phone/laptop to configure Wi-Fi!")
    print("="*50 + "\n")
    return ip

def main():
    print("\n=========================================")
    print("   ESP32 NETWORK SPEED CHECKER STARTING   ")
    print("=========================================\n")
    blink_led(4, 80)

    disp = DisplayManager(sda_pin=21, scl_pin=22)
    cfg = ConfigManager()
    tz_offset = cfg.config.get("timezone_offset_hours", 3)
    tester = SpeedTester(disp=disp, tz_offset_hours=tz_offset)
    server = WebServer(tester, cfg)

    ssid = cfg.config.get("wifi_ssid", "").strip()
    password = cfg.config.get("wifi_password", "")

    connected = False
    ip_addr = None

    if ssid:
        connected, ip_addr = connect_wifi(ssid, password, disp=disp)

    if not connected:
        ip_addr = start_access_point(
            cfg.config.get("ap_ssid", "ESP32-SpeedChecker"),
            cfg.config.get("ap_password", ""),
            disp=disp
        )

    # Start HTTP Web Server
    server.start(port=80)
    print(f"\n>> Dashboard ready at: http://{ip_addr}/ <<\n")

    # If already connected on boot, run an initial speed check after 2 seconds
    if connected:
        time.sleep(2)
        tester.run_full_test()

    last_auto_test = time.time()

    print("Listening for web requests and monitoring network... (Press Ctrl+C to stop)\n")

    while True:
        server.handle_client()

        # Check for on-demand test requested via web dashboard
        if tester.pending_test and not tester.is_running:
            tester.pending_test = False
            tester.run_full_test()
            last_auto_test = time.time()

        # Check for auto periodic test if connected
        interval_min = cfg.config.get("auto_test_interval_min", 30)
        interval_s = interval_min * 60
        now = time.time()

        # Keep server informed of next test countdown
        if interval_s > 0:
            elapsed = now - last_auto_test
            tester.next_test_in_s = max(0, int(interval_s - elapsed))
        else:
            tester.next_test_in_s = None

        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected() and not tester.is_running:
            if interval_s > 0 and (now - last_auto_test) >= interval_s:
                last_auto_test = now
                tester.run_full_test()

        time.sleep_ms(20)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Fatal error in main:", e)
