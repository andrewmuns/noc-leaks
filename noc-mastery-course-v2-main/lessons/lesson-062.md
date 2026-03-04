# Lesson 62: SIP REFER and Call Transfer

**Module 1 | Section 1.16 — SIP REFER and Call Transfer**
**⏱ ~6min read | Prerequisites: Lesson 42, Lesson 43**

---

## 1. Introduction to Call Transfers

Call transfer is one of the most widely used features in enterprise telephony. Whether it's a receptionist forwarding a call to the appropriate department, or an agent escalating a customer issue to a supervisor, call transfers happen millions of times daily across the world's phone networks.

In SIP, call transfers are accomplished using the **REFER** method, defined in RFC 3515. This method allows one party to instruct another party to initiate a new session with a specified target, effectively enabling third-party call control without requiring the transferring party to remain involved in the call.

There are two fundamental types of call transfers:

### Blind Transfer
In a blind transfer, the transferring party connects the caller directly to the target without first establishing a session with the target themselves. The transferor drops out immediately, and the caller hears ringing or announcements without knowing if the target is actually available.

### Attended Transfer
In an attended transfer, the transferor first establishes a separate call with the target, confirms they can take the call (perhaps consulting with them), and only then connects the original caller to the target. This allows for proper handoff and coordination.

Understanding these transfer types and how REFER works is essential for NOC engineers troubleshooting transfer failures in production environments.

---

## 2. The REFER Method and Message Flow

The REFER method is a SIP extension that requests a recipient to contact a third-party resource using the contact information provided in the request. When a REFER is sent, it effectively tells the recipient: "Contact this target on my behalf."

### Basic REFER Request

```
REFER sip:alice@atlanta.example.com SIP/2.0
Via: SIP/2.0/UDP pc33.atlanta.example.com;branch=z9hG4bKk12a10
From: <sip:bob@atlanta.example.com>;tag=190320
To: <sip:alice@atlanta.example.com>;tag=aaa10
Call-ID: a48c11e8@pc33.atlanta.example.com
CSeq: 23892 REFER
Contact: <sip:bob@pc33.atlanta.example.com>
Refer-To: <sip:carol@chicago.example.com>
Referred-By: <sip:bob@atlanta.example.com>
Content-Length: 0
```

The two most critical headers in a REFER request are:

- **Refer-To**: Specifies the target URI that the recipient should contact
- **Referred-By**: Indicates who is making the referral (for authentication and billing)

### Complete Transfer Flow

Here's the typical flow for a blind transfer (Alice refers Bob to Carol):

```
Alice                    Bob                     Carol
  |                       |                        |
  |<=====Dialog A========>|                        |
  |      (existing call)  |                        |
  |                       |                        |
  |<-----REFER Bob--------|                        |
  |    Refer-To: Carol    |                        |
  |-------202 Accepted--->|                        |
  |                       |    ----INVITE---->     |
  |                       |    Replaces: A         |
  |                       |                        |
  |                       |<----180 Ringing----    |
  |-------NOTIFY--------->|                        |
  |    (trying)           |                        |
  |                       |<----200 OK--------     |
  |                       |    ----ACK---->        |
  |                       |                        |
  |                       |<=====Dialog B========>|
  |                       |   (new call)           |
  |-------NOTIFY--------->|                        |
  |    (success)          |                        |
  |<=====Dialog A========>|                        |
  |     BYE / 200 OK      |                        |
  |                       |                        |
```

Key observations:
1. Bob receives the REFER and responds with 202 Accepted
2. Bob initiates a new INVITE to Carol, potentially using the Replaces header if this is a supervised transfer
3. Bob sends NOTIFY messages to Alice about the progress of the transfer
4. Once the transfer succeeds, the original dialog between Alice and Bob is terminated

---

## 3. Key Headers in Detail

### Refer-To Header

The Refer-To header is a mandatory header in REFER requests. It contains the URI that the recipient should contact.

```
Refer-To: <sip:carol@chicago.example.com>
```

It can also include additional parameters for more complex scenarios:

```
Refer-To: <sip:carol@chicago.example.com;transport=tls>
Refer-To: <sip:+15551234567@gateway.example.com;user=phone>
Refer-To: <sip:carol@chicago.example.com?Subject=Urgent%20Call>
```

When the Replaces parameter is needed (for attended transfers):

```
Refer-To: <sip:carol@chicago.example.com?Replaces=a48c11e8%40pc33.atlanta.example.com%3Bto-tag%3Dbbb20%3Bfrom-tag%3Dccc30>
```

The Replaces parameter indicates that the new dialog should replace an existing dialog, effectively bridging two calls together.

### Referred-By Header

The Referred-By header identifies who is making the referral:

```
Referred-By: <sip:bob@atlanta.example.com>
```

With a signature for security:

```
Referred-By: <sip:bob@atlanta.example.com>;cid="<bobrefer@atlanta.example.com>"
```

🔧 **NOC Tip:** The Referred-By header is crucial for billing and call detail records (CDRs). When investigating transfer-related billing disputes, always verify that the Referred-By header is correctly populated and preserved through proxy chains. Missing Referred-By headers can lead to incorrect billing attribution.

---

## 4. NOTIFY for Transfer Status

The REFER recipient must notify the sender about the status of the referenced request. This is done using NOTIFY requests containing the `message/sipfrag` content type.

### NOTIFY for Pending Transfer

```
NOTIFY sip:alice@atlanta.example.com SIP/2.0
Via: SIP/2.0/UDP pc33.atlanta.example.com;branch=z9hG4bKk93a10
From: <sip:bob@atlanta.example.com>;tag=190320
To: <sip:alice@atlanta.example.com>;tag=aaa10
Call-ID: a48c11e8@pc33.atlanta.example.com
CSeq: 102 NOTIFY
Event: refer
Subscription-State: active;expires=60
Content-Type: message/sipfrag;version=2.0
Content-Length: 23

SIP/2.0 100 Trying
```

### NOTIFY for Successful Transfer

```
NOTIFY sip:alice@atlanta.example.com SIP/2.0
Via: SIP/2.0/UDP pc33.atlanta.example.com;branch=z9hG4bKk94a10
From: <sip:bob@atlanta.example.com>;tag=190320
To: <sip:alice@atlanta.example.com>;tag=aaa10
Call-ID: a48c11e8@pc33.atlanta.example.com
CSeq: 103 NOTIFY
Event: refer
Subscription-State: terminated;reason=noresource
Content-Type: message/sipfrag;version=2.0
Content-Length: 23

SIP/2.0 200 OK
```

### NOTIFY for Failed Transfer

```
NOTIFY sip:alice@atlanta.example.com SIP/2.0
Via: SIP/2.0/UDP pc33.atlanta.example.com;branch=z9hG4bKk95a10
From: <sip:bob@atlanta.example.com>;tag=190320
To: <sip:alice@atlanta.example.com>;tag=aaa10
Call-ID: a48c11e8@pc33.atlanta.example.com
CSeq: 104 NOTIFY
Event: refer
Subscription-State: terminated;reason=rejected
Content-Type: message/sipfrag;version=2.0
Content-Length: 34

SIP/2.0 486 Busy Here
```

🔧 **NOC Tip:** When troubleshooting transfer failures, always check the NOTIFY bodies in your packet captures. The `message/sipfrag` content contains the actual response codes from the transfer attempt. A 486 Busy Here or 480 Temporarily Unavailable indicates the target couldn't accept the call, while a 404 Not Found suggests the Refer-To URI was invalid.

---

## 5. The Replaces Header and Attended Transfers

The Replaces header, defined in RFC 3891, is essential for attended transfers. It allows an INVITE to replace an existing dialog, effectively joining two calls together.

### Replaces Header Format

```
Replaces: <call-id>;to-tag=<tag>;from-tag=<tag>
```

Example:

```
INVITE sip:carol@chicago.example.com SIP/2.0
Via: SIP/2.0/UDP pc33.atlanta.example.com;branch=z9hG4bKk99a10
From: <sip:bob@atlanta.example.com>;tag=88820
To: <sip:carol@chicago.example.com>
Call-ID: transfer-attempt@pc33.atlanta.example.com
CSeq: 102 INVITE
Contact: <sip:bob@pc33.atlanta.example.com>
Replaces: bbb-ccc-ddd@chicago.example.com;to-tag=xyz789;from-tag=abc123
Content-Type: application/sdp
Content-Length: 142

v=0
o=bob 2890844526 2890844527 IN IP4 pc33.atlanta.example.com
s=-
c=IN IP4 pc33.atlanta.example.com
t=0 0
m=audio 49172 RTP/AVP 0
a=rtpmap:0 PCMU/8000
```

### Complete Attended Transfer Flow

```
Alice                    Bob                     Carol
  |                       |                        |
  |<=====Dialog A========>|                        |
  |      (with Alice)     |<=====Dialog B========>|
  |                       |      (with Carol)      |
  |                       |                        |
  |<-----REFER Bob--------|                        |
  | Refer-To: Carol       |                        |
  | (with Replaces: B)    |                        |
  |-------202 Accepted--->|                        |
  |                       |    ----INVITE---->     |
  |                       |    Replaces: B         |
  |                       |                        |
  |                       |<----200 OK--------     |
  |                       |    (replaces B)        |
  |                       |    ----ACK---->        |
  |                       |                        |
  |                       |<==Dialog C (replaces B)=>|
  |                       |                        |
  |-------NOTIFY--------->|                        |
  |    (success)          |                        |
  |<=====Dialog A]========|                        |
  |     BYE / 200 OK      |                        |
  |                       |                        |
```

With Replaces, when Bob INVITEs Carol and includes the Replaces header targeting Dialog B, Carol's UA will terminate Dialog B and use the new dialog with Bob. This effectively bridges Alice (still talking to Bob) with Carol.

---

## 6. Common Transfer Failures and Troubleshooting

### Transfer Loop Detection

Transfer loops occur when calls are repeatedly transferred between endpoints, potentially creating infinite loops. RFC 3515 suggests a Max-Forwards like mechanism using a `Refer-Count` or similar approach, but implementation varies.

Symptoms of transfer loops:
- Rapid sequential REFER messages
- Multiple NOTIFY messages in quick succession
- Call never establishing, cycling between endpoints

```
# Loop example in packet capture
REFER sip:alice@example.com -> bob@example.com (Refer-To: carol)
REFER sip:bob@example.com -> carol@example.com (Refer-To: alice)
REFER sip:carol@example.com -> alice@example.com (Refer-To: bob)
# Cycle repeats...
```

🔧 **NOC Tip:** Enable loop detection on your SBC or proxy. Most enterprise SBCs have configurable loop detection parameters. Set a maximum of 3-5 sequential transfers before rejecting further REFERs for a call. Look for `Max-Refer-Depth` or similar configuration options.

### Transfer Timeouts

Transfer timeouts can occur at multiple stages:

1. **REFER timeout**: No 202 Accepted received
2. **NOTIFY timeout**: 202 Accepted received, but no NOTIFY about progress
3. **Target timeout**: Target endpoint doesn't respond to INVITE

```
# Example: REFER timeout
T1 (Alice)              T2 (Bob)
  |----REFER------------->|
  |                      (wait ~64*T1 = ~3 seconds)
  |                      (retransmit REFER multiple times)
  |                      (final timeout, report failure)
  |<----408 Request Timeout (or internal failure)
```

### Endpoint Rejection

Endpoints may reject REFER requests for various reasons:

**403 Forbidden**: Endpoint not allowed to transfer
```
SIP/2.0 403 Forbidden
Warning: 399 atlanta.example.com "Transfer not permitted for this user"
```

**488 Not Acceptable Here**: Cannot process Refer-To URI
```
SIP/2.0 488 Not Acceptable Here
Warning: 399 atlanta.example.com "Unsupported URI scheme in Refer-To"
```

**501 Not Implemented**: REFER not supported
```
SIP/2.0 501 Not Implemented
```

### Debugging Transfers with sngrep

```bash
# Capture and filter transfer-related traffic
sngrep -r -k REFER,NOTIFY,INVITE,BYE port 5060

# Look for REFER subtraction
sngrep -r "REFER sip:" port 5060

# Analyze a specific call
sngrep -c "a48c11e8@pc33.atlanta.example.com"
```

### Debugging Transfers with tcpdump + Wireshark

```bash
# Capture to file for later analysis
tcpdump -i eth0 -w transfer_debug.pcap port 5060 or port 5061

# Filter for REFER methods
tshark -r transfer_debug.pcap -Y "sip.Method == \"REFER\""

# Show REFER and NOTIFY pairs
tshark -r transfer_debug.pcap -Y "sip.Method in {REFER NOTIFY}"
```

### Telnyx-Specific Transfer Debugging

```bash
# Check transfer-related call legs
GET /v2/calls/{call_control_id}/legs

# Review transfer attempts in call logs
GET /v2/calls?filter[answered_at_gte]={timestamp}

# Look for Refer-To handling in CDRs
# CDRs will show transfer_target and referred_by fields
```

---

## 7. Security Considerations

Transfer security is critical to prevent toll fraud and unauthorized call redirection.

### Authentication and Authorization

- Validate that the requesting party is authorized to transfer calls
- Check the Referred-By header against authenticated identity
- Implement transfer restrictions based on caller class of service

### URI Validation

```python
# Pseudocode for Refer-To validation
def validate_refer_to(uri):
    # Block transfers to premium rate numbers
    if is_premium_number(uri):
        return 403, "Premium destinations blocked"
    
    # Block transfers to external PSTN for internal users
    if is_pstn(uri) and not has_external_transfer_permission():
        return 403, "External transfers not authorized"
    
    # Validate URI format
    if not is_valid_sip_uri(uri):
        return 488, "Invalid URI format"
    
    return 200, "OK"
```

### Handling Malformed REFERs

```
# Missing Refer-To header (invalid request)
SIP/2.0 400 Bad Request
Warning: 399 proxy.example.com "Missing mandatory Refer-To header"

# Malformed Refer-To URI
SIP/2.0 400 Bad Request  
Warning: 399 proxy.example.com "Malformed Refer-To URI"
```

---

## 8. Key Takeaways

1. **Two Transfer Types**: Blind transfers drop the transferor immediately; attended transfers allow consultation before completion.

2. **REFER Method**: The SIP REFER method requests a recipient to contact a third party using the Refer-To URI.

3. **Key Headers**: Refer-To specifies the target, Referred-By identifies the transferor, and Replaces enables attended transfers by replacing existing dialogs.

4. **NOTIFY is Mandatory**: REFER recipients must send NOTIFY requests with sipfrag bodies to report transfer progress and final status.

5. **Loop Prevention**: Implement maximum transfer depth limits to prevent infinite transfer loops between endpoints.

6. **Common Failures**: Watch for 403/Forbidden (not authorized), 486/Busy (target unavailable), 408/Timeout (no response), and 488/Not Acceptable (URI issues).

7. **Security is Critical**: Validate Refer-To URIs, authenticate transfer requests, and restrict transfers based on user class of service.

8. **Debug Effectively**: Use sngrep to filter REFER/NOTIFY traffic and check NOTIFY bodies for actual transfer result codes.

---

Next: Lesson 60 — SIP Multiparty: Conferencing and the Focus Model
