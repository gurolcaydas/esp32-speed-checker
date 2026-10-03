import serial
import time
import os
import sys

PORT = 'COM4'
BAUD = 115200

def connect_serial():
    ser = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(0.2)
    # Interrupt running code with Ctrl+C
    ser.write(b'\r\x03\x03')
    time.sleep(0.4)
    ser.read_all()

    # Enter raw REPL: Ctrl+A
    ser.write(b'\r\x01')
    time.sleep(0.4)
    out = ser.read_all()
    if b'raw REPL; CTRL-B to exit' in out:
        return ser
    else:
        # Soft reset then raw REPL
        ser.write(b'\x04')
        time.sleep(0.8)
        ser.write(b'\r\x01')
        time.sleep(0.4)
        return ser

def upload_file(ser, local_path, remote_path):
    print(f"Uploading {local_path} -> {remote_path}...")
    with open(local_path, 'rb') as f:
        data = f.read()

    # Open remote file
    code_init = f"f = open('{remote_path}', 'wb')\n"
    ser.write(code_init.encode('utf-8') + b'\x04')
    ser.read_until(b'\x04>')

    # Write in chunks of 512 bytes
    chunk_size = 512
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        write_code = f"f.write({repr(chunk)})\n"
        ser.write(write_code.encode('utf-8') + b'\x04')
        ser.read_until(b'\x04>')

    code_close = "f.close()\n"
    ser.write(code_close.encode('utf-8') + b'\x04')
    ser.read_until(b'\x04>')
    print(f"  Done ({len(data)} bytes).")

def deploy(wifi_ssid=None, wifi_password=None):
    ser = connect_serial()
    print("Connected to ESP32 on COM4.")

    # Check if config.json exists on ESP32
    ser.write(b"import os; print('HAS_CFG:', 'config.json' in os.listdir())\n\x04")
    out = ser.read_until(b'\x04>').decode('utf-8', errors='replace')
    has_remote_cfg = 'HAS_CFG: True' in out

    if wifi_ssid is not None:
        import json
        cfg = {
            "wifi_ssid": wifi_ssid,
            "wifi_password": wifi_password or "",
            "target_servers": [{"host": "caydas.cloud", "port": 80}],
            "auto_test_interval_min": 5,
            "timezone_offset_hours": 3,
            "ap_ssid": "ESP32-ServerMonitor",
            "ap_password": ""
        }
        with open("config.json", "w") as f:
            json.dump(cfg, f, indent=2)
        upload_file(ser, "config.json", "config.json")
    elif not has_remote_cfg and os.path.exists("config.json"):
        upload_file(ser, "config.json", "config.json")
    elif has_remote_cfg:
        print("Preserving config.json on ESP32 (saved targets intact).")
        try:
            ser.write(b"f = open('config.json', 'r'); print('===CFG==='); print(f.read()); print('===ENDCFG==='); f.close()\n\x04")
            cfg_raw = ser.read_until(b'\x04>').decode('utf-8', errors='replace')
            if '===CFG===' in cfg_raw and '===ENDCFG===' in cfg_raw:
                remote_json = cfg_raw.split('===CFG===')[1].split('===ENDCFG===')[0].strip()
                with open("config.json", "w") as f:
                    f.write(remote_json)
                print("  Synced ESP32 config.json back to local PC.")
        except Exception as e:
            print("  Note: could not pull remote config:", e)

    files_to_upload = [
        ("config_manager.py", "config_manager.py"),
        ("ssd1306.py", "ssd1306.py"),
        ("display.py", "display.py"),
        ("speedtest.py", "speedtest.py"),
        ("webserver.py", "webserver.py"),
        ("index.html", "index.html"),
        ("main.py", "main.py"),
    ]

    for loc, rem in files_to_upload:
        if os.path.exists(loc):
            upload_file(ser, loc, rem)

    print("\nAll files uploaded successfully!")
    print("Restarting ESP32 to launch Network Speed Checker...\n")

    # Exit raw REPL: Ctrl+B
    ser.write(b'\x02')
    time.sleep(0.2)
    # Soft reboot: Ctrl+D
    ser.write(b'\x04')
    time.sleep(0.5)

    # Read initial boot output
    boot_log = ser.read(2048).decode('utf-8', errors='replace')
    print("--- ESP32 Boot Output ---")
    print(boot_log)
    print("-------------------------\n")
    ser.close()

if __name__ == '__main__':
    ssid = sys.argv[1] if len(sys.argv) > 1 else None
    pw = sys.argv[2] if len(sys.argv) > 2 else None
    deploy(ssid, pw)
