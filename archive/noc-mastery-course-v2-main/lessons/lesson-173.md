# Lesson 173: Shell Scripting for NOC — Practical Scripts
**Module 5 | Section 5.4 — Automation**
**⏱ ~7 min read | Prerequisites: Lesson 156**

---

## From Fundamentals to Real Scripts

Lesson 156 gave you the building blocks. Now let's build real tools that NOC engineers use daily. Each script here solves a real operational problem — adapt them to your environment.

## Script 1: Multi-Server Health Check with Report

This script checks service health across your fleet and generates a summary suitable for a shift handoff report.

```bash
#!/bin/bash
set -euo pipefail

# Configuration
SERVERS_FILE="/etc/noc/servers.txt"  # One server per line: hostname role
REPORT_DIR="/var/log/noc/health-reports"
TIMESTAMP=$(date '+%Y-%m-%d_%H%M%S')
REPORT="${REPORT_DIR}/health_${TIMESTAMP}.txt"

mkdir -p "$REPORT_DIR"

total=0
healthy=0
degraded=0
down=0

{
    echo "NOC Health Report — $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "================================================="
    echo ""

    while IFS=' ' read -r host role; do
        [[ "$host" =~ ^#.*$ || -z "$host" ]] && continue  # Skip comments and blank lines
        total=$((total + 1))
        echo -n "[$role] $host: "

        # Check connectivity
        if ! timeout 5 ssh -o ConnectTimeout=3 -o BatchMode=yes "$host" "true" 2>/dev/null; then
            echo "UNREACHABLE ❌"
            down=$((down + 1))
            continue
        fi

        # Gather metrics
        cpu=$(ssh "$host" "awk '{printf \"%.0f\", (1-\$5/(\$2+\$4+\$5))*100}' /proc/stat" 2>/dev/null || echo "N/A")
        mem=$(ssh "$host" "free | awk '/Mem:/{printf \"%.0f\", \$3/\$2*100}'" 2>/dev/null || echo "N/A")
        disk=$(ssh "$host" "df / | awk 'NR==2{print \$5}' | tr -d '%'" 2>/dev/null || echo "N/A")

        # Determine status
        status="OK ✅"
        if [[ "$cpu" != "N/A" && "$cpu" -gt 85 ]] || \
           [[ "$mem" != "N/A" && "$mem" -gt 90 ]] || \
           [[ "$disk" != "N/A" && "$disk" -gt 85 ]]; then
            status="DEGRADED ⚠️"
            degraded=$((degraded + 1))
        else
            healthy=$((healthy + 1))
        fi

        echo "${status} | CPU: ${cpu}% | MEM: ${mem}% | DISK: ${disk}%"
    done < "$SERVERS_FILE"

    echo ""
    echo "================================================="
    echo "Summary: ${total} servers | ${healthy} healthy | ${degraded} degraded | ${down} down"
} | tee "$REPORT"

# Exit with appropriate code for monitoring integration
[ "$down" -gt 0 ] && exit 2
[ "$degraded" -gt 0 ] && exit 1
exit 0
```

🔧 **NOC Tip:** Run this script at the start and end of every shift. The output files create an audit trail showing infrastructure health trends over time. Schedule it via cron every 30 minutes for continuous monitoring.

## Script 2: SIP Log Analyzer

Quickly parse SIP logs to identify error patterns — invaluable during incidents.

```bash
#!/bin/bash
set -euo pipefail

# SIP Error Analyzer
# Usage: ./sip-analyzer.sh [minutes_back] [log_file]

MINUTES=${1:-30}
LOGFILE=${2:-/var/log/kamailio/kamailio.log}
SINCE=$(date -d "${MINUTES} minutes ago" '+%Y-%m-%d %H:%M' 2>/dev/null || \
        date -v-${MINUTES}M '+%Y-%m-%d %H:%M')  # macOS fallback

echo "=== SIP Error Analysis — Last ${MINUTES} minutes ==="
echo "Log: ${LOGFILE}"
echo ""

# Extract recent log entries (simplified — adjust pattern for your log format)
RECENT=$(awk -v since="$SINCE" '$0 >= since' "$LOGFILE" 2>/dev/null || \
         tail -n 50000 "$LOGFILE")  # Fallback: last 50k lines

echo "--- Response Code Distribution ---"
echo "$RECENT" | grep -oP 'SIP/2\.0 \K\d{3}' | sort | uniq -c | sort -rn | head -15
echo ""

echo "--- Top Source IPs for 4xx/5xx ---"
echo "$RECENT" | grep -P 'SIP/2\.0 [45]\d{2}' | \
    grep -oP 'from\s+\K[\d.]+' | sort | uniq -c | sort -rn | head -10
echo ""

echo "--- Error Timeline (per 5-minute bucket) ---"
echo "$RECENT" | grep -P 'SIP/2\.0 [45]\d{2}' | \
    grep -oP '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}' | \
    awk -F: '{printf "%s:%s%d\n", $1, int($2/5)*5 < 10 ? "0" : "", int($2/5)*5}' | \
    sort | uniq -c
echo ""

echo "--- REGISTER Failure Sources (potential brute-force) ---"
echo "$RECENT" | grep "REGISTER" | grep -P '40[137]' | \
    grep -oP 'from\s+\K[\d.]+' | sort | uniq -c | sort -rn | head -5

echo ""
echo "Analysis complete."
```

This script produces output that immediately tells you: which error codes dominate, which sources generate errors, whether errors are increasing over time, and whether there's a brute-force registration attack.

## Script 3: Log Rotation and Disk Space Cleanup

Disk-full alerts at 3 AM are preventable. This script keeps log directories under control.

```bash
#!/bin/bash
set -euo pipefail

# Log Cleanup Script — run daily via cron
# 0 4 * * * /opt/noc-scripts/log-cleanup.sh >> /var/log/noc/cleanup.log 2>&1

LOG_DIRS=(
    "/var/log/kamailio:30"     # Keep 30 days
    "/var/log/rtpengine:14"    # Keep 14 days
    "/var/log/noc/reports:90"  # Keep 90 days
    "/tmp/pcaps:7"             # Keep 7 days
)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP] Starting log cleanup"

for entry in "${LOG_DIRS[@]}"; do
    dir="${entry%%:*}"
    days="${entry##*:}"

    if [ ! -d "$dir" ]; then
        echo "  SKIP: $dir (not found)"
        continue
    fi

    # Count files to be deleted
    count=$(find "$dir" -type f -mtime "+${days}" 2>/dev/null | wc -l)

    if [ "$count" -gt 0 ]; then
        # Show what would be deleted (dry run safety)
        echo "  CLEAN: $dir — removing $count files older than ${days} days"
        find "$dir" -type f -mtime "+${days}" -delete
    else
        echo "  OK: $dir — no files older than ${days} days"
    fi
done

# Report disk usage after cleanup
echo ""
echo "Disk usage after cleanup:"
df -h / /var /tmp 2>/dev/null | grep -v "^Filesystem"

echo "[$TIMESTAMP] Cleanup complete"
```

🔧 **NOC Tip:** Always log what cleanup scripts delete. When someone asks "where did the logs from two weeks ago go?" you need an answer. The cron redirect (`>> cleanup.log 2>&1`) captures everything.

## Script 4: Batch Service Operations with Safety

Rolling restart across multiple servers, with health checks between each.

```bash
#!/bin/bash
set -euo pipefail

# Rolling Restart Script
# Usage: ./rolling-restart.sh <service_name> <server1> [server2] ...

SERVICE=${1:?"Usage: $0 <service_name> <server1> [server2] ..."}
shift
SERVERS=("$@")

if [ ${#SERVERS[@]} -eq 0 ]; then
    echo "Error: No servers specified"
    exit 1
fi

echo "=== Rolling Restart: ${SERVICE} ==="
echo "Servers: ${SERVERS[*]}"
echo ""

# Safety confirmation
read -p "Proceed with rolling restart? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

FAILED=()

for SERVER in "${SERVERS[@]}"; do
    echo ""
    echo "--- Processing ${SERVER} ---"

    # Step 1: Pre-check
    echo -n "  Pre-check... "
    if ! ssh "$SERVER" "systemctl is-active ${SERVICE}" 2>/dev/null | grep -q "active"; then
        echo "SKIPPED (service not active — investigate manually)"
        FAILED+=("$SERVER")
        continue
    fi
    echo "OK"

    # Step 2: Drain (if applicable — remove from load balancer)
    echo "  Draining connections (30s wait)..."
    sleep 30

    # Step 3: Restart
    echo -n "  Restarting ${SERVICE}... "
    if ! ssh "$SERVER" "sudo systemctl restart ${SERVICE}" 2>/dev/null; then
        echo "FAILED ❌"
        FAILED+=("$SERVER")
        continue
    fi
    echo "OK"

    # Step 4: Health check with retry
    echo -n "  Waiting for health... "
    healthy=false
    for i in $(seq 1 12); do  # 12 attempts × 5 seconds = 60 second timeout
        sleep 5
        if ssh "$SERVER" "systemctl is-active ${SERVICE}" 2>/dev/null | grep -q "active"; then
            healthy=true
            break
        fi
        echo -n "."
    done

    if $healthy; then
        echo " HEALTHY ✅"
    else
        echo " NOT HEALTHY ❌ — STOPPING ROLLOUT"
        FAILED+=("$SERVER")
        echo ""
        echo "⚠️  Rollout halted at ${SERVER}. Remaining servers not restarted."
        echo "Failed servers: ${FAILED[*]}"
        exit 1
    fi

    echo "  ✅ ${SERVER} complete"
done

echo ""
echo "=== Rolling Restart Complete ==="
if [ ${#FAILED[@]} -gt 0 ]; then
    echo "⚠️  Failed servers: ${FAILED[*]}"
    exit 1
else
    echo "✅ All servers restarted successfully"
fi
```

This script embodies key operational safety patterns:
- **Confirmation prompt** — prevents accidental execution
- **Pre-checks** — verifies service is running before restarting
- **Drain period** — allows active connections to complete
- **Health verification** — confirms service is healthy after restart
- **Halt on failure** — stops the rollout if any server fails, preventing cascading damage

## Cron Scheduling

```bash
# Edit crontab
crontab -e

# Health check every 30 minutes
*/30 * * * * /opt/noc-scripts/health-check.sh >> /var/log/noc/health.log 2>&1

# Log cleanup daily at 4 AM
0 4 * * * /opt/noc-scripts/log-cleanup.sh >> /var/log/noc/cleanup.log 2>&1

# SIP analysis report every hour
0 * * * * /opt/noc-scripts/sip-analyzer.sh 60 >> /var/log/noc/sip-analysis.log 2>&1
```

🔧 **NOC Tip:** Always redirect cron output to a log file. Silent cron jobs that fail silently are a ticking time bomb. Monitor the log files or use a cron monitoring service that alerts when expected jobs don't run.

---

**Key Takeaways:**
1. Build scripts for tasks you do more than twice — the investment pays off immediately
2. Rolling restart scripts must include health checks and halt-on-failure logic
3. Log cleanup prevents disk-full emergencies — schedule it daily via cron
4. SIP log analysis scripts provide instant incident insight that would take 30+ minutes manually
5. Always include confirmation prompts and dry-run modes for destructive operations
6. Share scripts in a version-controlled team repository so the whole NOC benefits

**Next: Lesson 158 — Python Fundamentals for NOC Automation**
