# PulseForge

PulseForge is a lightweight Python daemon for monitoring website and API uptime, response latency, and health transitions in real time.

It checks configured endpoints on a timer, records every result in a local SQLite database, and sends webhook alerts only when an endpoint changes state between healthy and unhealthy.

## Why PulseForge?

- Zero dependencies
- Multi-threaded checks for faster monitoring
- Stores historical metrics locally in SQLite
- Detects only meaningful state changes to reduce alert fatigue
- Works with Discord, Slack, or custom webhook endpoints

## Features

- HTTP/HTTPS endpoint probing
- Response time tracking in milliseconds
- Status code capture
- Local SQLite logging
- Alert notifications on recoveries and outages
- Simple configuration through Python constants

## Example flow

- PulseForge checks each target on a fixed interval
- Each request records status, latency, and any error message
- If a service flips from healthy to unhealthy or vice versa, a webhook alert is sent
- Status changes are tracked without spamming repeated notifications

## Quick start

1. Clone the repository
2. Edit the configuration in `pulseforge.py`
3. Set your targets and webhook URL
4. Run the monitor

```bash
python pulseforge.py
```

## Configuration

At the top of `pulseforge.py`, you can configure:

```python
CHECK_INTERVAL_SECONDS = 30
REQUEST_TIMEOUT_SECONDS = 5
WEBHOOK_URL = ""

TARGETS = [
    "https://api.github.com",
    "https://cloudflare.com",
    "https://httpbin.org/status/200",
    "https://httpbin.org/status/503",
]
```

### Notes

- `WEBHOOK_URL` can be set to a Discord webhook, Slack incoming webhook, or any compatible HTTP endpoint.
- `TARGETS` is the list of services to monitor.
- `CHECK_INTERVAL_SECONDS` controls how often checks run.

## Project goal

PulseForge is built for simple, low-overhead monitoring of critical services without bringing in heavy infrastructure or external dependencies.

## License

This project is currently provided as-is for personal and experimental use.

## Short project description

Lightweight uptime and latency monitor with webhook alerts for service health changes.
