import usocket as socket
import ujson as json
import gc

class WebServer:
    def __init__(self, tester, config_manager):
        self.tester = tester
        self.config_manager = config_manager
        self.server_socket = None

    def start(self, port=80):
        gc.collect()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', port))
        self.server_socket.listen(3)
        self.server_socket.settimeout(0.2)
        print(f"Multi-Target Sentinel Web Dashboard started on port {port}")

    def send_file(self, cl, filepath, content_type="text/html"):
        cl.send(f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nConnection: close\r\n\r\n".encode('utf-8'))
        try:
            with open(filepath, 'rb') as f:
                buf = bytearray(1024)
                while True:
                    n = f.readinto(buf)
                    if not n or n <= 0:
                        break
                    cl.sendall(buf[:n])
        except Exception as e:
            print("Error serving file:", e)

    def handle_client(self):
        if not self.server_socket:
            return

        try:
            cl, addr = self.server_socket.accept()
        except OSError:
            return

        try:
            cl.settimeout(3.0)
            req_line = cl.readline().decode('utf-8', 'ignore')
            if not req_line:
                cl.close()
                return

            parts = req_line.split()
            if len(parts) < 2:
                cl.close()
                return

            method, path = parts[0], parts[1]

            content_length = 0
            while True:
                line = cl.readline().decode('utf-8', 'ignore')
                if line == '\r\n' or line == '\n' or not line:
                    break
                if line.lower().startswith('content-length:'):
                    try:
                        content_length = int(line.split(':')[1].strip())
                    except:
                        pass

            body = b""
            if content_length > 0:
                body = cl.read(content_length)

            if path == '/' or path == '/index.html':
                self.send_file(cl, 'index.html', 'text/html')
            elif path == '/api/status':
                last_res = self.tester.last_result or {}
                targets = self.config_manager.get_targets()
                data = {
                    "targets": targets,
                    "target": targets[0].get("host") if targets else "None",
                    "flag": last_res.get("flag", "ALL_ONLINE"),
                    "is_server_up": last_res.get("is_server_up", True),
                    "servers": last_res.get("servers", []),
                    "server": last_res.get("server", {}),
                    "internet": last_res.get("internet", {"avg": 0, "jitter": 0}),
                    "wifi": self.tester.get_wifi_info(),
                    "is_running": self.tester.is_running,
                    "last": self.tester.last_result,
                    "history": self.tester.history,
                    "stats": getattr(self.tester, "stats", {}),
                    "interval_min": self.config_manager.config.get("auto_test_interval_min", 5),
                    "next_test_in_s": getattr(self.tester, "next_test_in_s", None)
                }
                body_bytes = json.dumps(data).encode('utf-8')
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n")
                cl.sendall(body_bytes)
            elif path == '/api/target/add' and method == 'POST':
                try:
                    pld = json.loads(body.decode('utf-8'))
                    h = pld.get('host', '').strip()
                    pt = int(pld.get('port', 80))
                    if h:
                        self.config_manager.add_target(h, pt)
                        self.tester.set_targets(self.config_manager.get_targets())
                    cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{\"status\":\"added\"}")
                except Exception as e:
                    cl.send(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n")
            elif path == '/api/target/delete' and method == 'POST':
                try:
                    pld = json.loads(body.decode('utf-8'))
                    h = pld.get('host', '').strip()
                    pt = pld.get('port')
                    if h:
                        self.config_manager.delete_target(h, pt)
                        self.tester.set_targets(self.config_manager.get_targets())
                    cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{\"status\":\"deleted\"}")
                except Exception as e:
                    cl.send(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n")
            elif path == '/api/run' and method == 'POST':
                if not self.tester.is_running:
                    self.tester.pending_test = True
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{\"status\":\"started\"}")
            elif path == '/api/config' and method == 'POST':
                try:
                    cfg = json.loads(body.decode('utf-8'))
                    if 'interval_min' in cfg:
                        self.config_manager.update_interval(cfg.get('interval_min'))
                    if 'ssid' in cfg:
                        self.config_manager.update_wifi(cfg.get('ssid', ''), cfg.get('password', ''))
                    cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{\"status\":\"saved\"}")
                except Exception as e:
                    cl.send(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n")
            else:
                cl.send(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")
        except Exception as e:
            pass
        finally:
            try:
                cl.close()
            except:
                pass
            gc.collect()
