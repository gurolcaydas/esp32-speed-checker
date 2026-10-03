import ujson as json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "wifi_ssid": "",
    "wifi_password": "",
    "auto_test_interval_min": 30,
    "timezone_offset_hours": 3,
    "ap_ssid": "ESP32-SpeedChecker",
    "ap_password": ""
}

class ConfigManager:
    def __init__(self):
        self.config = self.load()

    def load(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
                # Ensure default keys exist
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
