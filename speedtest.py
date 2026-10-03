import usocket as socket
import utime as time
import ujson as json
import network
import gc

STATS_FILE = "stats.json"
HISTORY_FILE = "history.json"

class ServerMonitor:
    def __init__(self, disp=None, target_servers=None, tz_offset_hours=3):
        self.disp = disp
        self.target_servers = target_servers or [{"host": "caydas.cloud", "port": 80}]
        self.tz_offset_hours = tz_offset_hours
        self.stats = self._load_stats()
        self.history = self._load_history()
        self.last_result = self.history[-1] if self.history else None
        self.is_running = False
        self.pending_test = False
        self.next_test_in_s = None

    @property
    def target_server(self):
        if self.target_servers:
            return self.target_servers[0].get("host", "caydas.cloud")
        return "None"

    def set_targets(self, targets):
        if isinstance(targets, list):
            self.target_servers = targets

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
                    "date": "", "total": 0, "up": 0, "uptime_pct": 100.0,
                    "ping_min": 0.0, "ping_max": 0.0, "ping_sum": 0.0,
                    "servers": {}
                },
                "month": {
                    "month": "", "total": 0, "up": 0, "uptime_pct": 100.0,
                    "ping_min": 0.0, "ping_max": 0.0, "ping_sum": 0.0,
                    "servers": {}
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

    def get_wifi_info(self):
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            return {"connected": False, "ip": "0.0.0.0", "rssi": 0, "quality": "Disconnected", "percent": 0}
        
        rssi = 0
        try:
            rssi = wlan.status('rssi')
        except:
            pass

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

    def check_internet_ping(self, host="1.1.1.1", port=80, count=2):
        """Measures TCP ping to Cloudflare DNS reference."""
        times = []
        for _ in range(count):
            gc.collect()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.5)
            t_start = time.ticks_ms()
            try:
                addr = socket.getaddrinfo(host, port)[0][-1]
                s.connect(addr)
                t_diff = time.ticks_diff(time.ticks_ms(), t_start)
                times.append(t_diff)
            except Exception:
                pass
            finally:
                try:
                    s.close()
                except:
                    pass
            time.sleep_ms(40)

        if not times:
            return {"is_connected": False, "avg": 0, "min": 0, "max": 0, "jitter": 0}
        
        min_p = min(times)
        max_p = max(times)
        avg_p = sum(times) / len(times)
        return {
            "is_connected": True,
            "avg": round(avg_p, 1),
            "min": round(min_p, 1),
            "max": round(max_p, 1),
            "jitter": round(max_p - min_p, 1)
        }

    def check_server_health(self, host, port=80):
        """Performs TCP connection and HTTP health probe to target server."""
        gc.collect()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3.5)

        ping_ms = 0
        ttfb_ms = 0
        status_code = 0
        is_up = False
        error_msg = None

        t_start = time.ticks_ms()
        try:
            addr = socket.getaddrinfo(host, port)[0][-1]
            s.connect(addr)
            t_connected = time.ticks_ms()
            ping_ms = time.ticks_diff(t_connected, t_start)

            # Send HTTP HEAD probe
            req = f"HEAD / HTTP/1.1\r\nHost: {host}\r\nUser-Agent: ESP32-ServerSentinel/1.0\r\nConnection: close\r\n\r\n"
            s.send(req.encode('utf-8'))

            # Read status line
            resp_line = s.readline().decode('utf-8', 'ignore')
            t_responded = time.ticks_ms()
            ttfb_ms = time.ticks_diff(t_responded, t_start)

            if resp_line:
                parts = resp_line.split()
                if len(parts) >= 2:
                    try:
                        status_code = int(parts[1])
                    except:
                        status_code = 200
                else:
                    status_code = 200
            else:
                status_code = 200

            # 2xx, 3xx, 4xx are considered UP (server is alive and responding)
            is_up = (status_code >= 200 and status_code < 500)
        except Exception as e:
            error_msg = str(e)
            is_up = False
            status_code = 0
        finally:
            try:
                s.close()
            except:
                pass
            gc.collect()

        return {
            "server": host,
            "port": port,
            "is_up": is_up,
            "status_code": status_code,
            "ping_ms": round(ping_ms, 1) if is_up else 0,
            "response_time_ms": round(ttfb_ms, 1) if is_up else 0,
            "error": error_msg
        }

    def _update_stats(self, servers_res):
        t = self._get_local_time()
        today_str = "{:04d}-{:02d}-{:02d}".format(t[0], t[1], t[2])
        month_str = "{:04d}-{:02d}".format(t[0], t[1])

        all_up = all(s.get("is_up") for s in servers_res) if servers_res else False
        avg_ping = 0
        pings = [s["ping_ms"] for s in servers_res if s.get("is_up") and s.get("ping_ms", 0) > 0]
        if pings:
            avg_ping = round(sum(pings) / len(pings), 1)

        # 1. Today
        td = self.stats.get("today", {})
        if td.get("date") != today_str:
            td = {
                "date": today_str, "total": 0, "up": 0, "uptime_pct": 100.0,
                "ping_min": avg_ping, "ping_max": avg_ping, "ping_sum": 0.0,
                "servers": {}
            }
            self.stats["today"] = td

        td["total"] = td.get("total", 0) + 1
        if all_up:
            td["up"] = td.get("up", 0) + 1
        if avg_ping > 0:
            td["ping_min"] = avg_ping if td.get("ping_min", 0.0) <= 0 else min(td["ping_min"], avg_ping)
            td["ping_max"] = max(td.get("ping_max", 0.0), avg_ping)
            td["ping_sum"] = round(td.get("ping_sum", 0.0) + avg_ping, 1)
        td["uptime_pct"] = round((td["up"] / td["total"]) * 100.0, 1)

        # Per server breakdown
        td_srv = td.setdefault("servers", {})
        for s in servers_res:
            sh = s["server"]
            st = td_srv.setdefault(sh, {"total": 0, "up": 0, "uptime_pct": 100.0, "ping_min": 0, "ping_max": 0, "ping_sum": 0.0})
            st["total"] += 1
            if s.get("is_up"):
                st["up"] += 1
                sp = s.get("ping_ms", 0)
                if sp > 0:
                    st["ping_min"] = sp if st.get("ping_min", 0) <= 0 else min(st["ping_min"], sp)
                    st["ping_max"] = max(st.get("ping_max", 0), sp)
                    st["ping_sum"] = round(st.get("ping_sum", 0.0) + sp, 1)
            st["uptime_pct"] = round((st["up"] / st["total"]) * 100.0, 1)

        # 2. Month
        mo = self.stats.get("month", {})
        if mo.get("month") != month_str:
            mo = {
                "month": month_str, "total": 0, "up": 0, "uptime_pct": 100.0,
                "ping_min": avg_ping, "ping_max": avg_ping, "ping_sum": 0.0,
                "servers": {}
            }
            self.stats["month"] = mo

        mo["total"] = mo.get("total", 0) + 1
        if all_up:
            mo["up"] = mo.get("up", 0) + 1
        if avg_ping > 0:
            mo["ping_min"] = avg_ping if mo.get("ping_min", 0.0) <= 0 else min(mo["ping_min"], avg_ping)
            mo["ping_max"] = max(mo.get("ping_max", 0.0), avg_ping)
            mo["ping_sum"] = round(mo.get("ping_sum", 0.0) + avg_ping, 1)
        mo["uptime_pct"] = round((mo["up"] / mo["total"]) * 100.0, 1)

        mo_srv = mo.setdefault("servers", {})
        for s in servers_res:
            sh = s["server"]
            st = mo_srv.setdefault(sh, {"total": 0, "up": 0, "uptime_pct": 100.0, "ping_min": 0, "ping_max": 0, "ping_sum": 0.0})
            st["total"] += 1
            if s.get("is_up"):
                st["up"] += 1
                sp = s.get("ping_ms", 0)
                if sp > 0:
                    st["ping_min"] = sp if st.get("ping_min", 0) <= 0 else min(st["ping_min"], sp)
                    st["ping_max"] = max(st.get("ping_max", 0), sp)
                    st["ping_sum"] = round(st.get("ping_sum", 0.0) + sp, 1)
            st["uptime_pct"] = round((st["up"] / st["total"]) * 100.0, 1)

        self._save_stats()

    def run_full_test(self):
        if self.is_running:
            return {"status": "busy", "message": "Check already running"}

        self.is_running = True
        print("\n" + "="*45)
        print(f"  MULTI-TARGET SENTINEL CHECK ({len(self.target_servers)} targets)")
        print("="*45)

        # 1. Wi-Fi status
        wifi_info = self.get_wifi_info()

        # 2. Internet Ping (1.1.1.1)
        if self.disp:
            self.disp.show_testing("Gateway 1.1.1.1", progress_pct=25)
        net_res = self.check_internet_ping()
        print(f"Internet Gateway (1.1.1.1): {'ONLINE' if net_res['is_connected'] else 'OFFLINE'} ({net_res['avg']} ms)")

        # 3. Check each target server
        server_results = []
        tot_targets = len(self.target_servers)
        for idx, t in enumerate(self.target_servers):
            sh = t.get("host", "caydas.cloud")
            sp = t.get("port", 80)
            if self.disp:
                pct = int(35 + ((idx + 1) / max(1, tot_targets)) * 55)
                self.disp.show_testing(f"{sh[:12]}", progress_pct=pct)
            s_res = self.check_server_health(sh, sp)
            server_results.append(s_res)
            print(f"Server [{sh}]: {'UP' if s_res['is_up'] else 'DOWN'} | HTTP {s_res['status_code']} | Ping {s_res['ping_ms']} ms")

        # Determine overall flag
        up_count = sum(1 for s in server_results if s.get("is_up"))
        if not wifi_info['connected']:
            flag = "WIFI_DOWN"
        elif not net_res['is_connected']:
            flag = "NET_DOWN"
        elif up_count == len(server_results) and up_count > 0:
            flag = "ALL_ONLINE"
        elif up_count > 0:
            flag = "DEGRADED"
        elif not server_results:
            flag = "NO_TARGETS"
        else:
            flag = "ALL_OFFLINE"

        t_now = self._get_local_time()
        timestamp = "{:02d}:{:02d}:{:02d}".format(t_now[3], t_now[4], t_now[5])
        date_str = "{:04d}-{:02d}-{:02d}".format(t_now[0], t_now[1], t_now[2])
        short_time = "{:02d}:{:02d}".format(t_now[3], t_now[4])

        first_server = server_results[0] if server_results else {"server": "None", "ping_ms": 0, "status_code": 0, "is_up": False}

        result = {
            "timestamp": timestamp,
            "date": date_str,
            "short_time": short_time,
            "flag": flag,
            "is_server_up": (up_count > 0),
            "up_count": up_count,
            "total_targets": len(server_results),
            "servers": server_results,
            "target": first_server.get("server", "caydas.cloud"),
            "server": first_server,
            "internet": net_res,
            "wifi": wifi_info
        }

        self._update_stats(server_results)

        self.last_result = result
        self.history.append(result)
        if len(self.history) > 30:
            self.history.pop(0)
        self._save_history()

        # Update OLED Display
        if self.disp:
            self.disp.show_multi_server_status(
                servers=server_results,
                net_ms=net_res['avg'],
                rssi=wifi_info.get('rssi', -50),
                ip=wifi_info.get('ip', '0.0.0.0')
            )

        self.is_running = False
        print("="*45)
        print(f"  RESULT: [{flag}] {up_count}/{len(server_results)} Servers UP")
        print("="*45 + "\n")
        return result

# Maintain SpeedTester alias for compatibility
SpeedTester = ServerMonitor
