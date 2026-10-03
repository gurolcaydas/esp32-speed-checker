import ujson as json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "wifi_ssid": "",
    "wifi_password": "",
    "target_server": "caydas.cloud",
    "target_port": 80,
    "auto_test_interval_min": 5,
    "timezone_offset_hours": 3,
    "ap_ssid": "ESP32-ServerMonitor",
    "ap_password": ""
}

class ConfigManager:
    def __init__(self):
        self.config = self.load()

    def load(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in cfg:
                        cfg[k] = v
                return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()

    def save(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f)
            return True
        except Exception as e:
            print("Error saving config:", e)
            return False

    def update_wifi(self, ssid, password):
        self.config["wifi_ssid"] = ssid
        self.config["wifi_password"] = password
        self.save()

    def update_interval(self, interval_min):
        try:
            self.config["auto_test_interval_min"] = int(interval_min)
            self.save()
            return True
        except Exception as e:
            print("Error updating interval:", e)
            return False

    def update_target(self, server, port=80):
        try:
            self.config["target_server"] = server.strip()
            self.config["target_port"] = int(port)
            self.save()
            return True
        except Exception as e:
            print("Error updating target:", e)
            return False
