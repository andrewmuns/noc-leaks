# Lesson 175: Python for API Scripting — REST and GraphQL
**Module 5 | Section 5.4 — Automation**
**⏱ ~8 min read | Prerequisites: Lesson 158**

---

## APIs Are Your Remote Control

Modern telecom platforms like Telnyx expose REST APIs for everything: provisioning numbers, configuring SIP trunks, querying CDRs, managing messaging profiles. In Lesson 18, we covered HTTP and REST conceptually. Now we'll write Python scripts that use these APIs to automate NOC tasks.

The ability to script API calls transforms a NOC engineer from someone who clicks through dashboards to someone who can automate bulk operations, build custom monitoring, and integrate disparate systems.

## REST API Fundamentals in Python

### The HTTP Methods

```python
import requests

BASE_URL = "https://api.telnyx.com/v2"
HEADERS = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

# GET — retrieve data
response = requests.get(f"{BASE_URL}/phone_numbers", headers=HEADERS)

# POST — create a resource
response = requests.post(f"{BASE_URL}/number_orders", headers=HEADERS, json={
    "phone_numbers": [{"phone_number": "+15551234567"}]
})

# PATCH — update a resource
response = requests.patch(f"{BASE_URL}/phone_numbers/+15551234567",
    headers=HEADERS,
    json={"connection_id": "new-connection-id"}
)

# DELETE — remove a resource
response = requests.delete(f"{BASE_URL}/phone_numbers/+15551234567",
    headers=HEADERS
)
```

### Response Handling

```python
response = requests.get(f"{BASE_URL}/phone_numbers", headers=HEADERS)

# Always check the status code
if response.status_code == 200:
    data = response.json()
    for number in data["data"]:
        print(f"{number['phone_number']}: {number['status']}")
elif response.status_code == 401:
    print("Authentication failed — check your API key")
elif response.status_code == 429:
    print("Rate limited — slow down")
else:
    print(f"Unexpected response: {response.status_code}")
    print(response.text)
```

🔧 **NOC Tip:** Always log the full response body on errors, not just the status code. The body typically contains error details that explain exactly what went wrong — missing fields, invalid values, or permission issues.

## Handling Pagination

APIs return data in pages to avoid sending millions of records at once. You must iterate through all pages to get complete data.

```python
def get_all_pages(url, headers, params=None):
    """Fetch all pages from a paginated API endpoint."""
    all_records = []
    params = params or {}
    params.setdefault("page[size]", 250)
    page_number = 1

    while True:
        params["page[number]"] = page_number
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        records = data.get("data", [])
        all_records.extend(records)

        # Check if there are more pages
        meta = data.get("meta", {})
        total_pages = meta.get("total_pages", 1)

        if page_number >= total_pages:
            break
        page_number += 1

    return all_records

# Usage: get ALL phone numbers (could be thousands)
all_numbers = get_all_pages(
    f"{BASE_URL}/phone_numbers",
    HEADERS,
    params={"filter[status]": "active"}
)
print(f"Total active numbers: {len(all_numbers)}")
```

## Authentication Patterns

### API Key (Static)
Simplest approach — a fixed key in the header. Most Telnyx API operations use this.

```python
headers = {"Authorization": "Bearer YOUR_API_KEY"}
```

### OAuth 2.0 with Token Refresh
For APIs that issue short-lived tokens, your script needs to handle token refresh.

```python
import time

class APIClient:
    def __init__(self, client_id, client_secret, token_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.token = None
        self.token_expiry = 0

    def get_token(self):
        """Get a valid token, refreshing if expired."""
        if self.token and time.time() < self.token_expiry - 60:  # 60s buffer
            return self.token

        response = requests.post(self.token_url, data={
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        })
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        self.token_expiry = time.time() + data["expires_in"]
        return self.token

    def get(self, url, **kwargs):
        """Make an authenticated GET request."""
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.get_token()}"
        return requests.get(url, headers=headers, **kwargs)
```

## Rate Limiting and Retry Logic

APIs impose rate limits — exceeding them returns 429 Too Many Requests. A robust script handles this gracefully.

```python
import time
import random

def api_request_with_retry(method, url, max_retries=5, **kwargs):
    """Make an API request with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, timeout=30, **kwargs)

            if response.status_code == 429:
                # Rate limited — wait and retry
                retry_after = int(response.headers.get("Retry-After", 5))
                jitter = random.uniform(0, 1)  # Prevent thundering herd
                wait_time = retry_after + jitter
                print(f"Rate limited. Waiting {wait_time:.1f}s (attempt {attempt + 1})")
                time.sleep(wait_time)
                continue

            if response.status_code >= 500:
                # Server error — retry with exponential backoff
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Server error {response.status_code}. Retrying in {wait_time:.1f}s")
                time.sleep(wait_time)
                continue

            return response  # Success or client error (don't retry 4xx)

        except requests.ConnectionError:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Connection failed. Retrying in {wait_time:.1f}s")
            time.sleep(wait_time)

    raise Exception(f"Failed after {max_retries} retries: {method} {url}")
```

🔧 **NOC Tip:** The jitter (random delay) in retry logic is critical (as discussed in Lesson 147 on circuit breakers). Without it, all your scripts retry at exactly the same time after an outage, creating a retry storm that prevents recovery.

## Practical NOC Script: Bulk Number Audit

A real automation task — auditing all phone numbers to find configuration mismatches.

```python
#!/usr/bin/env python3
"""Audit all Telnyx phone numbers for configuration issues."""

import csv
import sys
from datetime import datetime

import requests

API_KEY = "YOUR_API_KEY"  # In production, use environment variables
BASE_URL = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def get_all_numbers():
    """Fetch all phone numbers with pagination."""
    numbers = []
    page = 1
    while True:
        resp = requests.get(f"{BASE_URL}/phone_numbers", headers=HEADERS,
                           params={"page[number]": page, "page[size]": 250})
        resp.raise_for_status()
        data = resp.json()
        numbers.extend(data["data"])
        if page >= data.get("meta", {}).get("total_pages", 1):
            break
        page += 1
    return numbers

def audit_number(number):
    """Check a number for common configuration issues."""
    issues = []
    phone = number["phone_number"]

    if not number.get("connection_id"):
        issues.append("No connection assigned")

    if number.get("messaging_profile_id") is None:
        issues.append("No messaging profile")

    if number.get("billing_group_id") is None:
        issues.append("No billing group")

    if number.get("emergency_enabled") and not number.get("emergency_address_id"):
        issues.append("E911 enabled but no address configured")

    return {"phone_number": phone, "status": number["status"], "issues": issues}

def main():
    print(f"Starting number audit at {datetime.now().isoformat()}")

    numbers = get_all_numbers()
    print(f"Found {len(numbers)} phone numbers")

    results = [audit_number(n) for n in numbers]
    issues_found = [r for r in results if r["issues"]]

    # Console summary
    print(f"\nAudit Results:")
    print(f"  Total numbers: {len(results)}")
    print(f"  Numbers with issues: {len(issues_found)}")

    for r in issues_found:
        print(f"  ⚠️  {r['phone_number']}: {', '.join(r['issues'])}")

    # CSV report
    report_file = f"number_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(report_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Phone Number", "Status", "Issues"])
        for r in results:
            writer.writerow([r["phone_number"], r["status"],
                           "; ".join(r["issues"]) if r["issues"] else "OK"])

    print(f"\nFull report saved to {report_file}")
    return 1 if issues_found else 0

if __name__ == "__main__":
    sys.exit(main())
```

## GraphQL: An Alternative API Paradigm

Some internal tools use GraphQL instead of REST. The key difference: with REST, you get fixed response shapes; with GraphQL, you request exactly the fields you need.

```python
def graphql_query(query, variables=None):
    """Execute a GraphQL query."""
    response = requests.post(
        "https://api.internal/graphql",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"query": query, "variables": variables or {}}
    )
    response.raise_for_status()
    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")
    return data["data"]

# Request exactly the fields you need
result = graphql_query("""
    query GetCarrierMetrics($carrierId: ID!, $since: DateTime!) {
        carrier(id: $carrierId) {
            name
            metrics(since: $since) {
                asr
                ner
                totalCalls
                avgDuration
            }
        }
    }
""", variables={"carrierId": "carrier-123", "since": "2024-01-15T00:00:00Z"})
```

## Security Best Practices

```python
import os

# NEVER hardcode API keys in scripts
API_KEY = os.environ.get("TELNYX_API_KEY")
if not API_KEY:
    print("Error: Set TELNYX_API_KEY environment variable")
    sys.exit(1)

# Use .env files for development (never commit them)
# pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()
```

---

**Key Takeaways:**
1. REST APIs use HTTP methods (GET/POST/PATCH/DELETE) mapped to CRUD operations
2. Always handle pagination — single API responses rarely contain all data
3. Implement retry with exponential backoff and jitter for robust API scripts
4. Never hardcode API keys — use environment variables or secret management
5. Log full error responses (not just status codes) for faster debugging
6. Bulk operations (audits, reports, provisioning) are where API scripting saves the most time

**Next: Lesson 160 — Python for Log Analysis and Data Processing**
