# Lesson 176: Python for Log Analysis and Data Processing
**Module 5 | Section 5.4 — Automation**
**⏱ ~7 min read | Prerequisites: Lesson 158**

---

## Beyond grep: Structured Log Analysis

In Lesson 156, we used grep, awk, and sed for quick log searches. These are perfect for ad-hoc investigation. But when you need to parse multi-line log entries, correlate events across files, or produce detailed statistical reports, Python provides the structure and power to handle complex analysis that would be nightmarish in Bash.

## Processing Large Log Files Efficiently

The cardinal rule: **never load an entire log file into memory**. Production log files can be gigabytes. Process them line by line using generators.

```python
def read_log_lines(filepath, encoding="utf-8"):
    """Generator that yields log lines without loading the entire file."""
    with open(filepath, encoding=encoding, errors="replace") as f:
        for line in f:
            yield line.rstrip("\n")

# Process a 10GB file using only a few KB of memory
error_count = 0
for line in read_log_lines("/var/log/kamailio/kamailio.log"):
    if "503 Service Unavailable" in line:
        error_count += 1
print(f"Total 503 errors: {error_count}")
```

### Filtering by Time Range

```python
from datetime import datetime

def parse_log_timestamp(line):
    """Extract timestamp from a log line. Adjust pattern for your format."""
    try:
        # Format: "2024-01-15 14:30:45.123 INFO ..."
        ts_str = line[:23]
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f")
    except (ValueError, IndexError):
        return None

def lines_in_timerange(filepath, start, end):
    """Yield only lines within the specified time range."""
    for line in read_log_lines(filepath):
        ts = parse_log_timestamp(line)
        if ts is None:
            continue
        if ts < start:
            continue
        if ts > end:
            break  # Assumes chronological order — stop early
        yield line, ts
```

🔧 **NOC Tip:** The `break` when we pass the end time is critical for performance. If you need the last 30 minutes from a day-long log file, you don't want to scan the entire file. For files that aren't sorted, remove the break, but know it'll be slower.

## Regular Expressions for Log Parsing

The `re` module is your scalpel for extracting structured data from unstructured log lines.

```python
import re

# Parse a SIP log line
SIP_PATTERN = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+'
    r'(?P<level>\w+)\s+'
    r'(?P<method>INVITE|REGISTER|BYE|CANCEL|ACK|OPTIONS)\s+'
    r'sip:(?P<destination>[^\s;>]+).*'
    r'From:\s*.*<sip:(?P<caller>[^@>]+)@.*'
    r'response:\s*(?P<sip_code>\d{3})?'
)

def parse_sip_log(line):
    """Parse a SIP log line into structured data."""
    match = SIP_PATTERN.search(line)
    if match:
        return match.groupdict()
    return None

# Simpler: extract just SIP response codes
CODE_PATTERN = re.compile(r'SIP/2\.0 (\d{3})')
codes = CODE_PATTERN.findall(log_content)
```

### Practical Pattern: Error Code Aggregation

```python
from collections import Counter, defaultdict
from datetime import datetime, timedelta

def analyze_sip_errors(log_path, minutes_back=60):
    """Analyze SIP error distribution in recent logs."""
    cutoff = datetime.now() - timedelta(minutes=minutes_back)
    code_counter = Counter()
    code_by_minute = defaultdict(Counter)
    source_by_code = defaultdict(Counter)

    code_pattern = re.compile(r'SIP/2\.0 (\d{3})')
    source_pattern = re.compile(r'src=(\d+\.\d+\.\d+\.\d+)')

    for line, ts in lines_in_timerange(log_path, cutoff, datetime.now()):
        code_match = code_pattern.search(line)
        if not code_match:
            continue

        code = code_match.group(1)
        if int(code) < 400:  # Only errors
            continue

        code_counter[code] += 1
        minute_bucket = ts.strftime("%H:%M")
        code_by_minute[minute_bucket][code] += 1

        source_match = source_pattern.search(line)
        if source_match:
            source_by_code[code][source_match.group(1)] += 1

    return code_counter, code_by_minute, source_by_code

# Usage
codes, timeline, sources = analyze_sip_errors("/var/log/kamailio/kamailio.log", 30)

print("Error Distribution:")
for code, count in codes.most_common(10):
    print(f"  {code}: {count}")
    top_sources = sources[code].most_common(3)
    for ip, src_count in top_sources:
        print(f"    └─ {ip}: {src_count}")
```

This produces output like:
```
Error Distribution:
  503: 1547
    └─ 10.0.1.45: 892
    └─ 10.0.1.46: 655
  408: 234
    └─ 203.0.113.50: 189
    └─ 198.51.100.23: 45
```

Immediately you see: 503s are coming from two internal IPs (probably overwhelmed SIP proxies), and 408s are dominated by a specific external IP (a customer endpoint that's timing out).

## Counter and defaultdict: Your Best Friends

```python
from collections import Counter, defaultdict

# Counter — count occurrences of anything
words = Counter()
for line in read_log_lines(log_path):
    words.update(line.split())
print("Most common words:", words.most_common(20))

# defaultdict — auto-initialize dictionary values
calls_per_carrier = defaultdict(int)
duration_per_carrier = defaultdict(list)

for cdr in parse_cdrs(cdr_file):
    calls_per_carrier[cdr["carrier"]] += 1
    duration_per_carrier[cdr["carrier"]].append(cdr["duration"])

# Calculate averages
for carrier, durations in duration_per_carrier.items():
    avg = sum(durations) / len(durations)
    total = calls_per_carrier[carrier]
    print(f"{carrier}: {total} calls, avg duration {avg:.1f}s")
```

## CSV Output for Reports

```python
import csv

def generate_error_report(codes, timeline, output_path):
    """Generate a CSV report of SIP error analysis."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Summary section
        writer.writerow(["Error Code", "Count", "Percentage"])
        total = sum(codes.values())
        for code, count in codes.most_common():
            pct = f"{count/total*100:.1f}%"
            writer.writerow([code, count, pct])

        writer.writerow([])  # Blank separator

        # Timeline section
        writer.writerow(["Time", "Total Errors"] +
                        [f"Code {c}" for c in sorted(codes.keys())])
        for minute in sorted(timeline.keys()):
            row = [minute, sum(timeline[minute].values())]
            for code in sorted(codes.keys()):
                row.append(timeline[minute].get(code, 0))
            writer.writerow(row)

    print(f"Report saved to {output_path}")
```

🔧 **NOC Tip:** CSV reports are universally readable — they open in Excel, Google Sheets, and can be attached to incident tickets. Always generate CSVs alongside console output for any analysis that might be shared.

## Correlating Across Multiple Log Files

Real investigations often require correlating events across different services using a shared identifier (call ID, request ID, trace ID).

```python
def correlate_by_call_id(sip_log, media_log, call_id):
    """Find all log entries related to a specific call across files."""
    results = {"sip": [], "media": []}

    for line in read_log_lines(sip_log):
        if call_id in line:
            results["sip"].append(line)

    for line in read_log_lines(media_log):
        if call_id in line:
            results["media"].append(line)

    return results

# Usage during incident investigation
call_id = "abc123-def456-ghi789"
logs = correlate_by_call_id(
    "/var/log/kamailio/kamailio.log",
    "/var/log/rtpengine/rtpengine.log",
    call_id
)

print(f"SIP events: {len(logs['sip'])}")
for line in logs["sip"]:
    print(f"  [SIP] {line[:120]}")

print(f"\nMedia events: {len(logs['media'])}")
for line in logs["media"]:
    print(f"  [RTP] {line[:120]}")
```

## Quick Pandas for Complex Analysis

When analysis gets complex — pivoting, joining, statistical operations — Pandas is the right tool.

```python
import pandas as pd

# Read CDRs into a DataFrame
df = pd.read_csv("cdrs.csv", parse_dates=["timestamp"])

# ASR by carrier for the last hour
recent = df[df["timestamp"] > pd.Timestamp.now() - pd.Timedelta(hours=1)]
asr = recent.groupby("carrier").agg(
    total=("call_id", "count"),
    answered=("status", lambda x: (x == "answered").sum())
)
asr["asr_pct"] = (asr["answered"] / asr["total"] * 100).round(2)
print(asr.sort_values("total", ascending=False))

# Time-bucketed analysis
df["minute"] = df["timestamp"].dt.floor("5min")
traffic = df.groupby("minute").size()
print(f"Peak traffic: {traffic.max()} calls at {traffic.idxmax()}")
```

Pandas is overkill for simple counting, but invaluable for multi-dimensional analysis, time series operations, and producing publication-quality reports.

---

**Key Takeaways:**
1. Process large log files with generators (line by line) — never load entire files into memory
2. Regular expressions with named groups turn unstructured logs into structured data
3. Counter and defaultdict are the essential tools for aggregating log data
4. Time-range filtering with early termination dramatically speeds up analysis
5. Cross-file correlation using call IDs connects signaling to media to billing events
6. Generate CSV reports for sharing — they open everywhere and preserve your analysis

**Next: Lesson 161 — Building NOC Runbooks — Structure and Best Practices**
