import ujson as json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "wifi_ssid": "",
    "wifi_password": "",
    "target_servers": [
        {"host": "caydas.cloud", "port": 80}
    ],
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
                # Backwards compatibility migration
                if "target_servers" not in cfg or not isinstance(cfg["target_servers"], list):
                    srv = cfg.get("target_server", "caydas.cloud")
                    port = cfg.get("target_port", 80)
                    cfg["target_servers"] = [{"host": srv, "port": port}]
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

    def get_targets(self):
        return self.config.get("target_servers", [{"host": "caydas.cloud", "port": 80}])

    def add_target(self, host, port=80):
        try:
            host = host.strip().replace("http://", "").replace("https://", "").split("/")[0]
            if not host:
                return False
            targets = list(self.get_targets())
            for t in targets:
                if t["host"].lower() == host.lower() and int(t.get("port", 80)) == int(port):
                    return True
            targets.append({"host": host, "port": int(port)})
            self.config["target_servers"] = targets
            return self.save()
        except Exception as e:
            print("Error adding target:", e)
            return False

    def delete_target(self, host, port=None):
        try:
            host = host.strip().lower()
            targets = self.get_targets()
            new_targets = []
            for t in targets:
                match_host = t["host"].lower() == host
                match_port = (port is None) or (int(t.get("port", 80)) == int(port))
                if not (match_host and match_port):
                    new_targets.append(t)
            self.config["target_servers"] = new_targets
            return self.save()
        except Exception as e:
            print("Error deleting target:", e)
            return False
