# Lesson 128: SIP 4xx Errors — Client-Side Failures

**Module 4 | Section 4.2 — SIP Debugging**
**⏱ ~8 min read | Prerequisites: Lesson 111, 40**

---

SIP 4xx responses indicate client errors — the request was valid but the server couldn't fulfill it. Understanding each 4xx code is essential because they have distinct causes and require distinct remediation. A 401 requires credentials. A 404 requires checking routing. A 408 requires checking reachability. This lesson maps each commonly encountered 4xx to its cause and solution.

## 401 Unauthorized — Authentication Required

**Meaning:** The request lacks valid authentication credentials. The server requires authentication and the client didn't provide it or provided invalid credentials.

**Typical flow:**
```
INVITE →
← 401 Unauthorized (with WWW-Authenticate header)
INVITE with Authorization →
← 200 OK
```

**Common causes:**
1. **No credentials sent**: Client didn't implement authentication, or credentials not configured
2. **Incorrect credentials**: Wrong password or key configured in the client
3. **Stale nonce**: Digest authentication nonce expired, client using cached response
4. **Clock skew**: Significant time difference between client and server (digest auth uses timestamps)

**Troubleshooting:**
1. Check if the second INVITE (with Authorization) exists:
   - If yes → Credentials are wrong
   - If no → Client isn't sending auth

2. Check the Authorization header:
   ```
   Authorization: Digest username="customer123",
     realm="sip.telnyx.com",
     nonce="d41d8cd98f00b204e9800998ecf8427e",
     uri="sip:+15551234567@sip.telnyx.com",
     response="9a4c3d...
   ```
   - Username matches the one in Telnyx portal?
   - Realm matches exactly (case-sensitive)?

3. Verify via Telnyx API:
   ```bash
   curl -H "Authorization: Bearer $TELNYX_API_KEY" \
        https://api.telnyx.com/v2/connections
   ```
   Check that the connection exists and is active.

**Resolution:**
- Client-side: Update credentials, check realm/username match
- Telnyx-side: Reset credentials, verify connection status

## 403 Forbidden — Authentication Succeeded but Not Authorized

**Meaning:** Credentials are valid, but this specific action is not permitted.

**Difference from 401:**
- 401: "Who are you?" (prove identity)
- 403: "I know who you are, but you can't do this" (prove authorization)

**Common causes:**
1. **IP ACL mismatch**: Source IP doesn't match allowed IPs for this credential
2. **Number not permitted**: Trying to use a number you don't own
3. **Destination blocked**: Trying to call a blocked destination (restrictions based on fraud prevention)
4. **Rate limit exceeded**: Too many requests, temporarily blocked
5. **Account suspended**: Billing issues, terms of service violations

**Troubleshooting:**
1. Check the source IP in the Via header:
   ```
   Via: SIP/2.0/UDP 203.0.113.5:5060
   ```
   Compare to the allowed IPs in the Telnyx connection settings.

2. Check the number being used:
   ```
   From: <sip:+15551234567@customer.com>
   ```
   Is this number assigned to this connection in the Telnyx portal?

3. Check Telnyx portal for account status.

🔧 **NOC Tip:** 403s due to IP ACL are common when customers change ISPs or add load balancers without updating their Telnyx connection configuration. When you see a 403 after "it was working before," ask: "Did your network change? New firewall? New IP?" The Via header shows their current IP — compare to what's configured.

## 404 Not Found — User Does Not Exist

**Meaning:** The requested user/number could not be found.

**Common causes:**
1. **Number not provisioned**: The dialed number isn't a valid number in Telnyx
2. **Routing translation failed**: Number manipulation resulted in an invalid number
3. **URI user not found**: The username in the URI doesn't exist
4. **Domain routing issue**: Request went to wrong domain

**Troubleshooting:**
1. Check the Request-URI:
   ```
   INVITE sip:+19998887777@telnyx.com SIP/2.0
   ```
   Is this number valid? Use Telnyx Number Lookup API to verify.

2. Check for outbound profiles:
   - Does the connection have an outbound voice profile?
   - Is there number translation that's stripping/modifying the dialed number?

3. Test with a known good number:
   - Call a number you know works
   - If 404 persists → Connection configuration issue
   - If 404 only for specific number → Number issue

## 408 Request Timeout — No Response Received

**Meaning:** The server sent a request but didn't receive a response within the timeout period.

**Common causes:**
1. **Client unreachable**: Client device is offline, behind a firewall blocking responses, or on a broken network path
2. **NAT/Firewall issue**: Response can't traverse back to client (Lessons 26-28)
3. **UDP packet loss**: INVITE or response lost in transit
4. **Timer misconfiguration**: Client's timer values don't match expected behavior
5. **Client not responding**: Client received INVITE but isn't sending responses (bug, overloaded)

**Troubleshooting:**
1. Check if the INVITE actually reached the customer:
   - If you see no response from customer at all → Network path or visibility issue
   - If you see responses but delayed → Network latency or packet loss

2. Check Contact and Via headers:
   ```
   Contact: <sip:user@192.168.1.5:5060>  ← Private IP
   Via: SIP/2.0/UDP 192.168.1.5:5060
   ```
   Private IPs behind NAT are the #1 cause of 408s.

3. Check for SIP ALG interference:
   - Some routers modify SIP headers badly
   - Via and Contact get modified incorrectly
   - Responses go to wrong addresses

🔧 **NOC Tip:** 408 is the most common SIP error for NAT traversal issues. When debugging, first check the Contact header in the REGISTER or INVITE. If it contains a private IP (10.x.x.x, 192.168.x.x, 172.16-31.x.x) and the customer is not in your datacenter, it's almost certainly a NAT problem. Telnyx's B2BUA handles this by latching to the source IP, but some configurations still break.

## 480 Temporarily Unavailable — Endpoint Not Reachable

**Meaning:** The callee exists but is currently not available (offline, unreachable, or routing failed).

**Common causes:**
1. **Endpoint offline**: Device powered off, lost network
2. **Registration expired**: Device's registration expired, server doesn't know where to route
3. **Not registered**: Endpoint never registered, server has no routing information
4. **Sequential forking exhausted**: Tried multiple destinations, none answered

**Troubleshooting:**
1. Check if the endpoint is registered:
   ```
   # Telnyx registration logs
   type:SIP AND method:REGISTER AND (From:"endpoint" OR Contact:"endpoint")
   ```

2. Check registration expiry:
   ```
   Expires: 3600
   ```
   If the last registration was >3600 seconds ago, it's expired.

3. Check for SIP heartbeat OPTIONS:
   - Is the server sending OPTIONS to check reachability?
   - Is the device responding?
   - 200 OK to OPTIONS = device is alive

## 486 Busy Here — Callee Active But Busy

**Meaning:** The callee is online and available, but currently busy (on another call, or user pressed "busy").

**This is normal user behavior** — not a technical issue. The distinction:
- 480: User is unavailable (can't be reached)
- 486: User is available but busy

**When 486s become a problem:**
1. If seen at very high rates for a single device → might be stuck in busy state
2. If customers report incorrect busy → device or PBX issue

**Troubleshooting:**
- Check if it's isolated to specific endpoints or widespread
- Verify the customer isn't experiencing phantom busy signals

## 487 Request Terminated — Call Was Cancelled

**Meaning:** The caller sent a CANCEL request before the call was answered.

**Typical flow:**
```
INVITE →
← 180 Ringing
(Caller hangs up)
CANCEL →
← 200 OK (to CANCEL)
← 487 Request Terminated
ACK →
```

**Common causes:**
1. **Caller gave up**: User hung up before answer
2. **Client timeout**: Client's internal timer fired before receiving answer
3. **Application timeout**: Application layer gave up waiting

**When 487 is a problem:**
- If 487s happen immediately after INVITE → Client timeout too short
- If 487s correlate with 180 but never 200s → Remote side not answering fast enough

🔧 **NOC Tip:** High 487 rates indicate customers are hanging up before calls connect. This could mean perceived poor quality (they expect calls to fail), long answer times, or application issues. Look at the time between INVITE and CANCEL — if it's consistent and short (~10 seconds), it might be a hardcoded client timeout. If it varies, it's probably user behavior.

## 488 Not Acceptable Here — Session Description Rejected

**Meaning:** The server or client can't accept the SDP session description (codec mismatch, media type issue).

**Common causes:**
1. **Codec mismatch**: No common codecs between offer and answer (Lessons 6-8)
2. **Media protocol mismatch**: One side wants RTP, other wants SRTP
3. **Invalid SDP**: Malformed session description
4. **Resource unavailable**: Server can't allocate RTP ports

**Troubleshooting:**
1. Check the SDP offer and answer:
   ```
   # Offer
   m=audio 10000 RTP/AVP 18 0 8
   # Answer
   m=audio 20000 RTP/AVP 101
   ```
   No matching codecs! The offer has G.729 (18), G.711 ulaw (0), G.711 alaw (8). The answer only has telephone-event (101).

2. Check crypto lines for SRTP:
   ```
   a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:...
   ```
   Is one side requiring SRTP while the other doesn't support it?

**Resolution:**
- Adjust codec configuration to include overlapping options
- Check SRTP requirements on both sides
- Verify SDP format compliance

---

**Key Takeaways:**

1. 401 = authentication required (check credentials, realm, nonce)
2. 403 = authorized but not permitted (check IP ACL, number ownership, account status)
3. 404 = number/user not found (check provisioning, routing translation)
4. 408 = timeout — most commonly NAT/firewall traversal issues (check Contact/Via headers)
5. 480 = temporarily unavailable — usually registration expiry or endpoint offline
6. 486 = busy — normal user behavior unless abnormally high rates
7. 487 = caller hung up — check if client timeouts are too aggressive
8. 488 = SDP/codec negotiation failure — verify codec overlap and SRTP compatibility

**Next: Lesson 113 — SIP 5xx/6xx Errors — Server and Global Failures**
