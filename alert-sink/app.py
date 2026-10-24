#!/usr/bin/env python3
# ==============================================================================
# Alert Sink Service - Nhận và lưu trữ cảnh báo Webhook từ Grafana Alerting
# Sinh viên: Ma Thị Thanh Tú - DTC245200587
# ==============================================================================

import os
import sys
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

LOG_FILE = "/var/log/alerts.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

class AlertSinkHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/health", "/healthz"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        elif self.path == "/alerts":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.wfile.write(b"No alerts yet.")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            alert_data = json.loads(post_body.decode("utf-8"))
        except Exception:
            alert_data = {"raw": post_body.decode("utf-8", errors="ignore")}

        status = alert_data.get("status", "unknown").upper()
        alerts = alert_data.get("alerts", [])
        alert_names = [a.get("labels", {}).get("alertname", "Unknown") for a in alerts]
        summary = ""
        if alerts:
            summary = alerts[0].get("annotations", {}).get("summary", "")

        log_msg = (
            f"\n{'='*70}\n"
            f"🚨 [ALERT-SINK] NHẬN CẢNH BÁO TỪ GRAFANA ALERTING LÚC: {timestamp}\n"
            f"   - Trạng thái : {status}\n"
            f"   - Tên cảnh báo: {', '.join(alert_names)}\n"
            f"   - Tóm tắt    : {summary}\n"
            f"   - Số lượng   : {len(alerts)} alerts trong payload\n"
            f"{'='*70}\n"
        )

        # In trực tiếp ra stdout (để Promtail và docker logs thu được)
        print(log_msg, flush=True)

        # Ghi log ra file để lưu trữ
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_msg)
            f.write(json.dumps(alert_data, indent=2, ensure_ascii=False))
            f.write("\n\n")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "received", "timestamp": timestamp}).encode("utf-8"))

    def log_message(self, format, *args):
        # Giảm ồn log HTTP thông thường
        sys.stderr.write(f"[HTTP] {self.address_string()} - {format % args}\n")

def run(server_class=HTTPServer, handler_class=AlertSinkHandler, port=5001):
    server_address = ("0.0.0.0", port)
    httpd = server_class(server_address, handler_class)
    print(f"[*] Alert-Sink Server đang lắng nghe webhook tại cổng {port}...", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == "__main__":
    run()
