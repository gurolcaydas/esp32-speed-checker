import usocket as socket
import utime as time
import ujson as json
import network
import gc

STATS_FILE = "stats.json"
HISTORY_FILE = "history.json"

class SpeedTester:
    def __init__(self, disp=None, tz_offset_hours=3):
        self.disp = disp
        self.tz_offset_hours = tz_offset_hours
        self.stats = self._load_stats()
        self.history = self._load_history()
        self.last_result = self.history[-1] if self.history else None
        self.is_running = False
        self.pending_test = False

    def _get_local_time(self):
        try:
            return time.localtime(time.time() + (self.tz_offset_hours * 3600))
        except Exception:
            return time.localtime()

    def _load_stats(self):
        try:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {
                "today": {
                    "date": "", "count": 0,
                    "down_max": 0.0, "down_min": 0.0,
                    "up_max": 0.0, "up_min": 0.0,
                    "ping_min": 0.0, "ping_max": 0.0,
                    "down_sum": 0.0, "up_sum": 0.0, "ping_sum": 0.0
                },
                "month": {
                    "month": "", "count": 0,
                    "down_max": 0.0, "down_min": 0.0,
                    "up_max": 0.0, "up_min": 0.0,
                    "ping_min": 0.0, "ping_max": 0.0,
                    "down_sum": 0.0, "up_sum": 0.0, "ping_sum": 0.0
                }
            }

    def _save_stats(self):
        try:
            with open(STATS_FILE, "w") as f:
                json.dump(self.stats, f)
        except Exception as e:
            print("Error saving stats:", e)

    def _load_history(self):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_history(self):
        try:
            with open(HISTORY_FILE, "w") as f:
                json.dump(self.history, f)
        except Exception as e:
            print("Error saving history:", e)

    def _update_stats(self, down_mbps, up_mbps, ping_avg):
        t = self._get_local_time()
        today_str = "{:04d}-{:02d}-{:02d}".format(t[0], t[1], t[2])
        month_str = "{:04d}-{:02d}".format(t[0], t[1])

        # 1. Update Today stats
        td = self.stats.get("today", {})
        if td.get("date") != today_str:
            td = {
                "date": today_str, "count": 0,
                "down_max": down_mbps, "down_min": down_mbps,
                "up_max": up_mbps, "up_min": up_mbps,
                "ping_min": ping_avg, "ping_max": ping_avg,
                "down_sum": 0.0, "up_sum": 0.0, "ping_sum": 0.0
            }
            self.stats["today"] = td

        td["count"] = td.get("count", 0) + 1
        td["down_max"] = max(td.get("down_max", 0.0), down_mbps)
        td["down_min"] = down_mbps if td.get("down_min", 0.0) <= 0 else min(td["down_min"], down_mbps)
        td["up_max"] = max(td.get("up_max", 0.0), up_mbps)
        td["up_min"] = up_mbps if td.get("up_min", 0.0) <= 0 else min(td["up_min"], up_mbps)
        if ping_avg > 0:
            td["ping_min"] = ping_avg if td.get("ping_min", 0.0) <= 0 else min(td["ping_min"], ping_avg)
            td["ping_max"] = max(td.get("ping_max", 0.0), ping_avg)
        td["down_sum"] = round(td.get("down_sum", 0.0) + down_mbps, 2)
        td["up_sum"] = round(td.get("up_sum", 0.0) + up_mbps, 2)
        td["ping_sum"] = round(td.get("ping_sum", 0.0) + ping_avg, 2)

        # 2. Update Month stats
        mo = self.stats.get("month", {})
        if mo.get("month") != month_str:
            mo = {
                "month": month_str, "count": 0,
                "down_max": down_mbps, "down_min": down_mbps,
                "up_max": up_mbps, "up_min": up_mbps,
                "ping_min": ping_avg, "ping_max": ping_avg,
                "down_sum": 0.0, "up_sum": 0.0, "ping_sum": 0.0
            }
            self.stats["month"] = mo

        mo["count"] = mo.get("count", 0) + 1
        mo["down_max"] = max(mo.get("down_max", 0.0), down_mbps)
        mo["down_min"] = down_mbps if mo.get("down_min", 0.0) <= 0 else min(mo["down_min"], down_mbps)
        mo["up_max"] = max(mo.get("up_max", 0.0), up_mbps)
        mo["up_min"] = up_mbps if mo.get("up_min", 0.0) <= 0 else min(mo["up_min"], up_mbps)
        if ping_avg > 0:
            mo["ping_min"] = ping_avg if mo.get("ping_min", 0.0) <= 0 else min(mo["ping_min"], ping_avg)
            mo["ping_max"] = max(mo.get("ping_max", 0.0), ping_avg)
        mo["down_sum"] = round(mo.get("down_sum", 0.0) + down_mbps, 2)
        mo["up_sum"] = round(mo.get("up_sum", 0.0) + up_mbps, 2)
        mo["ping_sum"] = round(mo.get("ping_sum", 0.0) + ping_avg, 2)

        self._save_stats()

    def get_wifi_info(self):
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            return {"connected": False, "ip": "0.0.0.0", "rssi": 0, "quality": "Disconnected"}
        
        rssi = 0
        try:
            rssi = wlan.status('rssi')
        except:
            pass

        # Quality estimation based on dBm
        if rssi >= -50:
            quality = "Excellent"
            percent = 100
        elif rssi >= -60:
            quality = "Very Good"
            percent = 85
        elif rssi >= -70:
            quality = "Good"
            percent = 70
        elif rssi >= -80:
            quality = "Fair"
            percent = 50
        else:
            quality = "Weak"
            percent = max(10, 100 + rssi)

        ip = wlan.ifconfig()[0]
        return {
            "connected": True,
            "ip": ip,
            "rssi": rssi,
            "quality": quality,
            "percent": percent
        }

    def measure_ping(self, host="1.1.1.1", port=80, count=4):
        """Measures TCP connection handshake latency."""
        times = []
        for _ in range(count):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3.0)
            t_start = time.ticks_ms()
            try:
                addr = socket.getaddrinfo(host, port)[0][-1]
                s.connect(addr)
                t_end = time.ticks_ms()
                diff = time.ticks_diff(t_end, t_start)
                times.append(diff)
            except Exception as e:
                pass
            finally:
                try:
                    s.close()
                except:
                    pass
            time.sleep_ms(100)

        if not times:
            return {"min": 0, "avg": 0, "max": 0, "jitter": 0, "loss": 100}

        min_p = min(times)
        max_p = max(times)
        avg_p = sum(times) / len(times)
        jitter = max_p - min_p
        loss = round(((count - len(times)) / count) * 100, 1)

        return {
            "min": round(min_p, 1),
            "avg": round(avg_p, 1),
            "max": round(max_p, 1),
            "jitter": round(jitter, 1),
            "loss": loss
        }

    def measure_download(self, host="speed.cloudflare.com", port=80, path="/__down?bytes=1048576"):
        """Downloads a test payload and calculates throughput in Mbps."""
        gc.collect()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(12.0)
        
        try:
            addr = socket.getaddrinfo(host, port)[0][-1]
            s.connect(addr)
            
            req = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: ESP32-SpeedTest/1.0\r\nConnection: close\r\n\r\n"
            s.send(req.encode('utf-8'))

            # Skip HTTP response headers
            header_done = False
            header_bytes = bytearray()
            while not header_done:
                ch = s.read(1)
                if not ch:
                    break
                header_bytes.extend(ch)
                if header_bytes.endswith(b"\r\n\r\n"):
                    header_done = True

            # Stream payload with 4KB buffer for high throughput
            buf = bytearray(4096)
            total_bytes = 0
            t_start = time.ticks_ms()

            while True:
                n = s.readinto(buf)
                if not n or n <= 0:
                    break
                total_bytes += n

            t_end = time.ticks_ms()
            duration_ms = time.ticks_diff(t_end, t_start)

            if duration_ms <= 0 or total_bytes == 0:
                return {"mbps": 0.0, "bytes": total_bytes, "duration_s": 0.0}

            duration_s = duration_ms / 1000.0
            # bits / seconds / 1,000,000 = Mbps
            mbps = (total_bytes * 8.0) / (duration_s * 1000000.0)
            return {
                "mbps": round(mbps, 2),
                "bytes": total_bytes,
                "duration_s": round(duration_s, 2)
            }
        except Exception as e:
            print("Download test error:", e)
            return {"mbps": 0.0, "bytes": 0, "duration_s": 0.0, "error": str(e)}
        finally:
            try:
                s.close()
            except:
                pass
            gc.collect()

    def measure_upload(self, host="speed.cloudflare.com", port=80, path="/__up", size_bytes=262144):
        """Uploads a test payload and calculates throughput in Mbps (default 256KB)."""
        gc.collect()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(12.0)
        
        try:
            addr = socket.getaddrinfo(host, port)[0][-1]
            s.connect(addr)

            req_hdr = (
                f"POST {path} HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                f"User-Agent: ESP32-SpeedTest/1.0\r\n"
                f"Content-Type: application/octet-stream\r\n"
                f"Content-Length: {size_bytes}\r\n"
                f"Connection: close\r\n\r\n"
            )
            s.send(req_hdr.encode('utf-8'))

            # Send in 2KB blocks
            chunk = b"X" * 2048
            bytes_sent = 0
            t_start = time.ticks_ms()

            while bytes_sent < size_bytes:
                to_send = min(len(chunk), size_bytes - bytes_sent)
                s.send(chunk[:to_send])
                bytes_sent += to_send

            # Read back response
            s.recv(256)
            t_end = time.ticks_ms()
            duration_ms = time.ticks_diff(t_end, t_start)
            duration_s = max(0.001, duration_ms / 1000.0)

            mbps = (bytes_sent * 8.0) / (duration_s * 1000000.0)
            return {
                "mbps": round(mbps, 2),
                "bytes": bytes_sent,
                "duration_s": round(duration_s, 2)
            }
        except Exception as e:
            print("Upload test error:", e)
            return {"mbps": 0.0, "bytes": 0, "duration_s": 0.0, "error": str(e)}
        finally:
            try:
                s.close()
            except:
                pass
            gc.collect()

    def run_full_test(self):
        if self.is_running:
            return {"status": "busy", "message": "Test already in progress"}
        
        self.is_running = True
        print("\n" + "="*45)
        print("  ESP32 NETWORK SPEED TEST STARTED")
        print("="*45)

        wifi_info = self.get_wifi_info()
        print(f"Wi-Fi Status: {wifi_info['quality']} (RSSI: {wifi_info['rssi']} dBm, IP: {wifi_info['ip']})")

        # 1. Latency / Ping
        if self.disp:
            self.disp.show_testing("1/3 Ping Latency", progress_pct=30)
        print("Measuring Latency (Ping) to Cloudflare (1.1.1.1)...")
        ping_res = self.measure_ping()
        print(f"  Ping: {ping_res['avg']} ms (Min: {ping_res['min']} ms, Max: {ping_res['max']} ms, Jitter: {ping_res['jitter']} ms)")

        # 2. Download
        if self.disp:
            self.disp.show_testing("2/3 Download 1MB", progress_pct=65)
        print("Testing Download Speed (Cloudflare CDN 1MB)...")
        down_res = self.measure_download()
        print(f"  Download Speed: {down_res['mbps']} Mbps ({round(down_res['bytes']/1024, 1)} KB in {down_res['duration_s']}s)")

        # 3. Upload
        if self.disp:
            self.disp.show_testing("3/3 Upload 256KB", progress_pct=90)
        print("Testing Upload Speed (256KB)...")
        up_res = self.measure_upload()
        print(f"  Upload Speed:   {up_res['mbps']} Mbps ({round(up_res['bytes']/1024, 1)} KB in {up_res['duration_s']}s)")

        t_now = self._get_local_time()
        timestamp = "{:02d}:{:02d}:{:02d}".format(t_now[3], t_now[4], t_now[5])
        date_str = "{:04d}-{:02d}-{:02d}".format(t_now[0], t_now[1], t_now[2])
        short_time = "{:02d}:{:02d}".format(t_now[3], t_now[4])

        result = {
            "timestamp": timestamp,
            "date": date_str,
            "short_time": short_time,
            "wifi": wifi_info,
            "ping": ping_res,
            "download": down_res,
            "upload": up_res,
            "rating": self._calculate_rating(down_res['mbps'], ping_res['avg'])
        }

        self._update_stats(down_res['mbps'], up_res['mbps'], ping_res['avg'])

        self.last_result = result
        self.history.append(result)
        if len(self.history) > 20:
            self.history.pop(0)
        self._save_history()

        if self.disp:
            self.disp.show_results(
                down_res['mbps'],
                up_res['mbps'],
                ping_res['avg'],
                wifi_info['ip'],
                wifi_info.get('rssi', -50)
            )

        self.is_running = False
        print("="*45)
        print(f"  SUMMARY: {down_res['mbps']} Mbps Down | {up_res['mbps']} Mbps Up | {ping_res['avg']} ms Ping")
        print("="*45 + "\n")
        return result

    def _calculate_rating(self, download_mbps, ping_ms):
        if download_mbps >= 15 and ping_ms < 50:
            return "Ultra Fast"
        elif download_mbps >= 8 and ping_ms < 90:
            return "Great"
        elif download_mbps >= 3 and ping_ms < 150:
            return "Good"
        elif download_mbps > 0:
            return "Fair / Slow"
        else:
            return "Failed"
