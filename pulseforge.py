import concurrent.futures
import json
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

# --- Configuration ---
CHECK_INTERVAL_SECONDS = 30
REQUEST_TIMEOUT_SECONDS = 5
WEBHOOK_URL = ""  # Set to a Discord/Slack/Custom incoming webhook endpoint

TARGETS = [
    "https://api.github.com",
    "https://cloudflare.com",
    "https://httpbin.org/status/200",
    "https://httpbin.org/status/503",  # Sample failing target
]


@dataclass
class ProbeResult:
    url: str
    status_code: int
    latency_ms: float
    is_up: bool
    error_message: Optional[str] = None


class Database:
    def __init__(self, db_path: str = "pulseforge.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    status_code INTEGER,
                    latency_ms REAL,
                    is_up INTEGER NOT NULL,
                    error_message TEXT,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def record(self, result: ProbeResult):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO metrics (url, status_code, latency_ms, is_up, error_message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    result.url,
                    result.status_code,
                    result.latency_ms,
                    1 if result.is_up else 0,
                    result.error_message,
                ),
            )
            conn.commit()


class Notifier:
    @staticmethod
    def send_alert(url: str, transition: str, status_code: int, latency_ms: float):
        if not WEBHOOK_URL:
            return

        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "target": url,
            "event": transition,
            "status_code": status_code,
            "latency_ms": round(latency_ms, 2),
        }

        try:
            req = urllib.request.Request(
                WEBHOOK_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "PulseForge-Notifier/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                pass
        except Exception as e:
            print(f"[!] Failed to deliver webhook: {e}")


def probe_endpoint(url: str) -> ProbeResult:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PulseForge-Agent/1.0"},
        method="GET",
    )
    start_time = time.perf_counter()

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            latency = (time.perf_counter() - start_time) * 1000
            status = response.getcode()
            is_up = 200 <= status < 400
            return ProbeResult(
                url=url,
                status_code=status,
                latency_ms=latency,
                is_up=is_up,
            )
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - start_time) * 1000
        return ProbeResult(
            url=url,
            status_code=e.code,
            latency_ms=latency,
            is_up=False,
            error_message=f"HTTP Error: {e.code}",
        )
    except Exception as e:
        latency = (time.perf_counter() - start_time) * 1000
        return ProbeResult(
            url=url,
            status_code=0,
            latency_ms=latency,
            is_up=False,
            error_message=str(e),
        )


def run_monitor():
    db = Database()
    state_tracker: Dict[str, bool] = {}

    print(f"[*] PulseForge started. Tracking {len(TARGETS)} targets.")

    while True:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(probe_endpoint, TARGETS))

        for res in results:
            db.record(res)
            previous_state = state_tracker.get(res.url)

            # State transition handling
            if previous_state is not None and previous_state != res.is_up:
                event = "RECOVERED" if res.is_up else "OUTAGE"
                print(f"[ALERT] {res.url} -> {event} ({res.status_code}) [{res.latency_ms:.2f}ms]")
                Notifier.send_alert(res.url, event, res.status_code, res.latency_ms)
            else:
                tag = "OK" if res.is_up else "FAIL"
                print(f"[{tag}] {res.url} - {res.status_code} - {res.latency_ms:.1f}ms")

            state_tracker[res.url] = res.is_up

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        run_monitor()
    except KeyboardInterrupt:
        print("\n[*] PulseForge stopped.")
      
