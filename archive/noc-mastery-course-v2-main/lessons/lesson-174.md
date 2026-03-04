# Lesson 174: Python Fundamentals for NOC Automation
**Module 5 | Section 5.4 — Automation**
**⏱ ~8 min read | Prerequisites: Lesson 156**

---

## When Bash Isn't Enough

In Lessons 156–157, you built shell scripts that solve real NOC problems. Bash is perfect for gluing commands together, processing text files, and quick automation. But when you need to interact with REST APIs, parse complex JSON, handle errors gracefully, or build tools with proper argument handling, Bash becomes painful.

The rule of thumb: **if your Bash script exceeds 50 lines, or if it needs to parse JSON or make HTTP calls, rewrite it in Python.**

Python is the lingua franca of DevOps and infrastructure automation. It's readable, has an enormous standard library, and a rich ecosystem of third-party packages. Most importantly for NOC engineers — it's installed on virtually every Linux server.

## Python Basics for the Shell-Experienced

If you know Bash, Python will feel natural with a few adjustments.

### Variables and Types

```python
# No declaration needed, no dollar signs
hostname = "sip-proxy-01"
port = 5060
is_healthy = True
carriers = ["CarrierA", "CarrierB", "CarrierC"]
server_info = {"hostname": "sip-proxy-01", "cpu": 45.2, "status": "active"}

# f-strings for formatting (Python 3.6+)
print(f"Checking {hostname} on port {port}")
print(f"CPU usage: {server_info['cpu']:.1f}%")
```

### Data Structures

```python
# Lists — ordered, mutable
servers = ["sip-proxy-01", "sip-proxy-02", "sip-proxy-03"]
servers.append("sip-proxy-04")
for server in servers:
    print(f"Checking {server}")

# Dictionaries — key-value pairs (JSON-like)
metrics = {
    "asr": 52.3,
    "ner": 98.7,
    "cps": 145,
    "active_calls": 3200
}
print(f"ASR: {metrics['asr']}%")

# List comprehensions — powerful one-liners
healthy = [s for s in servers if check_health(s)]
error_counts = {code: count for code, count in raw_data if count > 10}
```

### Functions

```python
def check_server_health(hostname, port=8080, timeout=5):
    """Check if a server's health endpoint responds."""
    try:
        response = requests.get(
            f"http://{hostname}:{port}/health",
            timeout=timeout
        )
        return response.status_code == 200
    except requests.ConnectionError:
        return False

# Usage
if check_server_health("sip-proxy-01"):
    print("Server is healthy")
```

## Error Handling: try/except

Error handling is where Python dramatically outshines Bash. Instead of checking exit codes, you catch specific exceptions.

```python
import json
import requests

def get_carrier_status(carrier_id):
    """Fetch carrier status from the API with proper error handling."""
    try:
        response = requests.get(
            f"https://api.internal/carriers/{carrier_id}/status",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
            timeout=10
        )
        response.raise_for_status()  # Raises exception for 4xx/5xx
        return response.json()

    except requests.Timeout:
        print(f"Timeout connecting to API for carrier {carrier_id}")
        return None
    except requests.ConnectionError:
        print(f"Cannot connect to API — is the service running?")
        return None
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} — {e.response.text}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON response from API")
        return None
```

🔧 **NOC Tip:** Always catch specific exceptions rather than bare `except:`. Catching everything hides bugs. If you don't know what exceptions a function raises, let it crash — the traceback tells you exactly what to handle.

## Essential Libraries

### requests — HTTP Made Simple

```python
import requests

# GET request
response = requests.get("https://api.telnyx.com/v2/phone_numbers",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    params={"page[size]": 50}
)
data = response.json()
for number in data["data"]:
    print(f"{number['phone_number']} — {number['status']}")

# POST request
response = requests.post("https://api.telnyx.com/v2/calls",
    headers={
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    },
    json={
        "connection_id": "abc123",
        "to": "+15551234567",
        "from": "+15559876543"
    }
)
```

### json — Parsing and Formatting

```python
import json

# Parse JSON string
raw = '{"call_id": "abc123", "duration": 45, "status": "completed"}'
data = json.loads(raw)
print(f"Call {data['call_id']} lasted {data['duration']}s")

# Write JSON to file
with open("report.json", "w") as f:
    json.dump(metrics, f, indent=2)

# Pretty print for debugging
print(json.dumps(api_response, indent=2))
```

### datetime — Time Calculations

```python
from datetime import datetime, timedelta, timezone

# Current time in UTC
now = datetime.now(timezone.utc)

# Time arithmetic
one_hour_ago = now - timedelta(hours=1)
next_maintenance = now + timedelta(days=7, hours=2)

# Parse timestamps from logs
log_time = datetime.strptime("2024-01-15 14:30:45", "%Y-%m-%d %H:%M:%S")

# Format for display
print(now.strftime("%Y-%m-%d %H:%M:%S %Z"))

# ISO format for APIs
print(now.isoformat())  # 2024-01-15T14:30:45+00:00
```

### csv — Report Generation

```python
import csv

# Write a CSV report
with open("carrier_report.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Carrier", "ASR", "NER", "Total Calls"])
    writer.writerow(["CarrierA", "52.3%", "98.7%", 15234])
    writer.writerow(["CarrierB", "48.1%", "97.2%", 8923])

# Read a CSV file
with open("cdrs.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if int(row["duration"]) > 3600:
            print(f"Long call: {row['call_id']} — {row['duration']}s")
```

## Virtual Environments: Isolating Dependencies

Never install Python packages globally on production servers. Use virtual environments.

```bash
# Create a virtual environment
python3 -m venv ~/noc-tools-env

# Activate it
source ~/noc-tools-env/bin/activate

# Install packages (only affects this environment)
pip install requests pyyaml tabulate

# Save dependencies
pip freeze > requirements.txt

# Deactivate when done
deactivate
```

🔧 **NOC Tip:** Create one virtual environment for all your NOC scripts (`~/noc-tools-env`). Add `source ~/noc-tools-env/bin/activate` to your `.bashrc` so it's always available. Include a `requirements.txt` in your scripts repository so other engineers can replicate the setup.

## A Complete NOC Tool: Server Fleet Status

```python
#!/usr/bin/env python3
"""NOC Fleet Status Tool — checks all servers and generates a report."""

import sys
import json
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

SERVERS = [
    {"host": "sip-proxy-01", "role": "SIP Proxy", "check_port": 5060},
    {"host": "sip-proxy-02", "role": "SIP Proxy", "check_port": 5060},
    {"host": "media-01", "role": "Media Server", "check_port": 2223},
    {"host": "media-02", "role": "Media Server", "check_port": 2223},
    {"host": "db-primary", "role": "Database", "check_port": 5432},
    {"host": "db-replica-01", "role": "Database Replica", "check_port": 5432},
]

def check_server(server):
    """Check a single server and return its status."""
    host = server["host"]
    result = {"host": host, "role": server["role"]}

    try:
        # Check SSH connectivity and gather metrics
        cmd = f"ssh -o ConnectTimeout=5 {host} 'uptime; free -m | grep Mem; df -h / | tail -1'"
        output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)

        if output.returncode != 0:
            result["status"] = "unreachable"
            return result

        lines = output.stdout.strip().split("\n")
        result["status"] = "healthy"
        result["uptime"] = lines[0].strip() if len(lines) > 0 else "unknown"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
    except Exception as e:
        result["status"] = f"error: {str(e)}"

    return result

def main():
    print(f"=== Fleet Status Report — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    # Check all servers in parallel (much faster than sequential)
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_server, s): s for s in SERVERS}
        for future in as_completed(futures):
            results.append(future.result())

    # Sort by role for readability
    results.sort(key=lambda r: r["role"])

    # Display results
    healthy = 0
    for r in results:
        icon = "✅" if r["status"] == "healthy" else "❌"
        if r["status"] == "healthy":
            healthy += 1
        print(f"  {icon} [{r['role']}] {r['host']}: {r['status']}")

    print(f"\nSummary: {healthy}/{len(results)} servers healthy")

    # Save JSON for programmatic consumption
    with open("/tmp/fleet-status.json", "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "results": results}, f, indent=2)

    return 0 if healthy == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
```

Key Python advantages visible here:
- **ThreadPoolExecutor** — checks all servers in parallel (10x faster than sequential Bash loops)
- **Structured error handling** — each failure type is caught and reported
- **JSON output** — machine-readable for integration with other tools
- **Clean argument parsing** — expandable with `argparse` for complex options

## Bash vs. Python Decision Guide

| Task | Use Bash | Use Python |
|------|----------|------------|
| Run a few commands in sequence | ✅ | |
| Grep/awk text processing | ✅ | |
| API calls with JSON parsing | | ✅ |
| Complex logic with error handling | | ✅ |
| Parallel operations | | ✅ |
| Data manipulation / calculations | | ✅ |
| Quick one-liners | ✅ | |
| Tools shared across the team | | ✅ |

---

**Key Takeaways:**
1. Switch from Bash to Python when scripts exceed 50 lines or need JSON/API interaction
2. The `requests` library makes HTTP API calls simple — essential for modern telecom APIs
3. Always use try/except with specific exceptions for robust error handling
4. Virtual environments isolate dependencies — never install packages globally on production
5. ThreadPoolExecutor enables parallel operations that are 10x faster than sequential Bash loops
6. Save structured output (JSON) alongside human-readable output for tool integration

**Next: Lesson 159 — Python for API Scripting — REST and GraphQL**
