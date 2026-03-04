# Lesson 172: Shell Scripting Fundamentals for NOC
**Module 5 | Section 5.4 — Automation**
**⏱ ~8 min read | Prerequisites: Lessons 1-5**

---

## Why Every NOC Engineer Needs Shell Skills

At 3 AM, when an alert fires and you need to check the status of 20 services across 10 servers, you have two choices: manually SSH into each server one by one (taking 30+ minutes), or run a script that does it in 10 seconds. Shell scripting is the NOC engineer's superpower — it turns repetitive manual work into automated, repeatable, and auditable procedures.

You don't need to be a software engineer. You need to know enough Bash to automate the tasks you do every shift.

## Bash Fundamentals

### Variables and String Handling

```bash
#!/bin/bash

# Variables — no spaces around the equals sign!
HOSTNAME="sip-proxy-01"
PORT=5060
LOG_DIR="/var/log/kamailio"

# String interpolation
echo "Checking ${HOSTNAME} on port ${PORT}"

# Command substitution — capture command output
CURRENT_TIME=$(date '+%Y-%m-%d %H:%M:%S')
CALL_COUNT=$(grep -c "INVITE sip:" ${LOG_DIR}/kamailio.log)

echo "[$CURRENT_TIME] Active INVITEs: ${CALL_COUNT}"
```

### Conditionals

```bash
# Check if a service is responding
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health | grep -q "200"; then
    echo "Service is healthy"
else
    echo "SERVICE DOWN — escalate!"
    exit 1
fi

# Numeric comparisons
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d. -f1)
if [ "$CPU_USAGE" -gt 85 ]; then
    echo "WARNING: CPU at ${CPU_USAGE}%"
fi

# String comparisons
STATUS=$(systemctl is-active kamailio)
if [ "$STATUS" = "active" ]; then
    echo "Kamailio is running"
elif [ "$STATUS" = "inactive" ]; then
    echo "Kamailio is STOPPED"
fi
```

### Loops

```bash
# Check multiple servers
SERVERS="sip-proxy-01 sip-proxy-02 sip-proxy-03 media-01 media-02"
for SERVER in $SERVERS; do
    echo -n "Checking ${SERVER}... "
    if ssh "$SERVER" "systemctl is-active kamailio" 2>/dev/null | grep -q "active"; then
        echo "OK"
    else
        echo "FAILED ❌"
    fi
done

# Process a log file line by line
while IFS= read -r line; do
    if echo "$line" | grep -q "503 Service Unavailable"; then
        echo "Found 503: $line"
    fi
done < /var/log/sip/errors.log
```

## Exit Codes: The Language of Success and Failure

Every command returns an exit code: 0 means success, non-zero means failure. This is how scripts make decisions.

```bash
# $? contains the last command's exit code
grep -q "ERROR" /var/log/app.log
if [ $? -eq 0 ]; then
    echo "Errors found in log"
fi

# Shorter form with && and ||
grep -q "CRITICAL" /var/log/app.log && echo "CRITICAL errors found!"
ping -c 1 -W 2 sip-proxy-01 > /dev/null || echo "sip-proxy-01 is unreachable!"
```

🔧 **NOC Tip:** Always check exit codes in scripts. A script that ignores failures will happily continue after a critical step fails, potentially making the situation worse.

## Script Safety: set -euo pipefail

The single most important line in any NOC script:

```bash
#!/bin/bash
set -euo pipefail
```

What this does:
- **`-e`**: Exit immediately if any command fails (non-zero exit)
- **`-u`**: Treat unset variables as errors (catches typos)
- **`-o pipefail`**: A pipeline fails if ANY command in it fails (not just the last)

Without this, a script continues silently after failures:

```bash
# DANGEROUS — without set -e
cd /var/log/old_logs    # Fails if directory doesn't exist
rm -rf *                 # Runs in the CURRENT directory instead!

# SAFE — with set -e
set -euo pipefail
cd /var/log/old_logs    # Script exits here if directory doesn't exist
rm -rf *                 # Never reached
```

## Pipes and Redirection: Chaining Commands

The pipe (`|`) is the most powerful concept in Unix. It connects the output of one command to the input of another.

```bash
# Find the top 10 SIP error codes in the last hour
grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')" /var/log/sip/messages.log \
    | grep -oP 'SIP/2\.0 \K[4-6]\d{2}' \
    | sort \
    | uniq -c \
    | sort -rn \
    | head -10

# Output:
#   1547 503
#    892 408
#    234 486
#     67 404
```

This one-liner replaces what would take 10 minutes of manual log reading. Let's break it down:
1. `grep` filters log lines from the last hour
2. `grep -oP` extracts just the SIP response codes (4xx, 5xx, 6xx)
3. `sort` groups identical codes together
4. `uniq -c` counts consecutive identical lines
5. `sort -rn` sorts by count, descending
6. `head -10` shows only the top 10

## Essential Text Processing Tools

### grep — Finding Patterns

```bash
# Find all 503 responses
grep "503 Service Unavailable" /var/log/sip/messages.log

# Count occurrences
grep -c "503" /var/log/sip/messages.log

# Show context (2 lines before and after)
grep -B2 -A2 "CRITICAL" /var/log/app.log

# Recursive search across files
grep -r "connection refused" /var/log/
```

### awk — Column Extraction and Processing

```bash
# Extract the 5th column (IP addresses from access logs)
awk '{print $5}' /var/log/sip/access.log

# Sum a numeric column
awk '{sum += $3} END {print "Total duration:", sum}' cdrs.csv

# Filter and format
awk -F',' '$4 > 300 {printf "Long call: %s → %s (%d sec)\n", $2, $3, $4}' cdrs.csv
```

### sed — Stream Editing

```bash
# Replace in-place
sed -i 's/old_carrier/new_carrier/g' config.txt

# Extract between patterns
sed -n '/START_INCIDENT/,/END_INCIDENT/p' /var/log/app.log

# Delete blank lines
sed '/^$/d' report.txt
```

### cut — Simple Column Extraction

```bash
# Extract fields from CSV
cut -d',' -f1,3,5 cdrs.csv

# Extract from colon-delimited files
cut -d: -f1 /etc/passwd
```

## A Complete NOC Script Example

```bash
#!/bin/bash
set -euo pipefail

# NOC Health Check Script
# Checks all SIP proxies and reports status

SERVERS="sip-proxy-{01..06}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
FAILURES=0

echo "=== NOC Health Check — ${TIMESTAMP} ==="
echo ""

for i in $(seq -w 01 06); do
    SERVER="sip-proxy-${i}"
    echo -n "  ${SERVER}: "

    # Check SSH connectivity
    if ! ssh -o ConnectTimeout=5 "$SERVER" "true" 2>/dev/null; then
        echo "UNREACHABLE ❌"
        FAILURES=$((FAILURES + 1))
        continue
    fi

    # Check service status
    STATUS=$(ssh "$SERVER" "systemctl is-active kamailio" 2>/dev/null || echo "unknown")
    CPU=$(ssh "$SERVER" "top -bn1 | grep 'Cpu(s)' | awk '{print \$2}'" 2>/dev/null || echo "N/A")
    CONNS=$(ssh "$SERVER" "ss -s | grep 'TCP:' | awk '{print \$2}'" 2>/dev/null || echo "N/A")

    if [ "$STATUS" = "active" ]; then
        echo "OK ✅ | CPU: ${CPU}% | TCP Conns: ${CONNS}"
    else
        echo "DOWN ❌ (status: ${STATUS})"
        FAILURES=$((FAILURES + 1))
    fi
done

echo ""
if [ "$FAILURES" -gt 0 ]; then
    echo "⚠️  ${FAILURES} server(s) have issues — investigate immediately"
    exit 1
else
    echo "✅ All servers healthy"
    exit 0
fi
```

🔧 **NOC Tip:** Save scripts like this in a shared `~/noc-scripts/` directory. When a new engineer joins, they inherit a toolkit instead of starting from scratch. Version control them in Git (covered in Lesson 97).

## Common Pitfalls

1. **Unquoted variables**: `rm $FILE` fails if filename has spaces. Always `rm "$FILE"`
2. **Missing error handling**: Check return codes, especially for SSH and network commands
3. **Hardcoded paths**: Use variables at the top of the script for easy customization
4. **No logging**: Add timestamps and output to a log file for audit trails
5. **Running untested scripts in production**: Always test with `echo` or `--dry-run` first

---

**Key Takeaways:**
1. `set -euo pipefail` at the top of every script prevents silent failures
2. Pipes chain simple commands into powerful one-liners for log analysis
3. grep, awk, sed, and cut are the four essential text processing tools
4. Always quote variables and check exit codes for robust scripts
5. Build a shared script library — each script saves hours across the team over time
6. Test scripts with dry-run mode before executing in production

**Next: Lesson 157 — Shell Scripting for NOC — Practical Scripts**
