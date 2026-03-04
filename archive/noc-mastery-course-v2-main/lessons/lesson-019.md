# Lesson 19: TLS — How Encryption Works for SIP and HTTPS

**Module 1 | Section 1.4 — Protocol Stack**
**⏱ ~9 min read | Prerequisites: Lesson 16**

---

## Why TLS Matters for Telecom

Every SIP message contains sensitive information: who's calling whom, phone numbers, IP addresses, authentication credentials. Without encryption, anyone on the network path can read this data. TLS (Transport Layer Security) encrypts the communication channel, providing **confidentiality** (no eavesdropping), **integrity** (no tampering), and **authentication** (you're talking to who you think you are).

For Telnyx NOC engineers, TLS is everywhere:
- **SIP over TLS (SIPS):** Encrypted SIP signaling on port 5061
- **HTTPS:** API calls, webhook delivery, web portal access
- **gRPC:** Internal service communication
- **WebSocket Secure (WSS):** Real-time event streaming

Understanding TLS means understanding why connections fail, why certificates expire, and how to debug handshake errors.

## The TLS Handshake: Step by Step

### TLS 1.2 Handshake (Still Common)

```
Client                                Server
  |                                     |
  |--- ClientHello ------------------>  |  (supported ciphers, random)
  |                                     |
  |<-- ServerHello -------------------  |  (chosen cipher, random)
  |<-- Certificate -------------------  |  (server's X.509 cert)
  |<-- ServerKeyExchange -------------  |  (DH parameters)
  |<-- ServerHelloDone ---------------  |
  |                                     |
  |--- ClientKeyExchange ------------>  |  (client's DH public value)
  |--- ChangeCipherSpec ------------->  |  (switching to encrypted)
  |--- Finished (encrypted) -------->  |
  |                                     |
  |<-- ChangeCipherSpec --------------  |
  |<-- Finished (encrypted) ---------  |
  |                                     |
  |=== Application Data (encrypted) ==  |
```

This is **2 round trips** before encrypted data flows. At 70ms RTT (transatlantic), that's 140ms just for the TLS handshake, on top of TCP's 70ms handshake — 210ms total before the first SIP message.

**What happens at each step:**

1. **ClientHello:** "Here are the cipher suites I support, my random nonce, and the TLS versions I speak."
2. **ServerHello:** "I've chosen this cipher suite and here's my random nonce."
3. **Certificate:** "Here's my certificate proving I'm sip.telnyx.com."
4. **Key Exchange:** Both sides contribute to generating a shared secret using Diffie-Hellman. Neither side ever transmits the actual encryption key.
5. **Finished:** Both sides verify that the handshake wasn't tampered with.

### TLS 1.3: Faster and Simpler

TLS 1.3 reduced the handshake to **1 round trip**:

```
Client                                Server
  |                                     |
  |--- ClientHello + KeyShare ------->  |
  |                                     |
  |<-- ServerHello + KeyShare --------  |
  |<-- EncryptedExtensions -----------  |
  |<-- Certificate -------------------  |
  |<-- CertificateVerify -------------  |
  |<-- Finished ----------------------  |
  |                                     |
  |--- Finished --------------------->  |
  |                                     |
  |=== Application Data (encrypted) ==  |
```

The client sends its key share in the first message (guessing which key exchange algorithm the server will choose). If it guesses right, the handshake completes in one round trip — saving 70ms on a transatlantic connection.

TLS 1.3 also removed insecure options: no RSA key exchange (no forward secrecy), no CBC mode ciphers, no RC4, no MD5. Fewer choices means fewer ways to misconfigure.

🔧 **NOC Tip:** If a SIP device only supports TLS 1.0 or 1.1 (deprecated), it will fail to connect to servers that require TLS 1.2+. The handshake will fail immediately. In Wireshark, you'll see a ClientHello with an old TLS version followed by a fatal alert or connection reset. This is common with older IP phones and ATAs.

## Certificate Chains: Trust Hierarchy

TLS authentication relies on **X.509 certificates** organized in a trust hierarchy:

```
Root CA (trusted by OS/browser)
  └── Intermediate CA (signed by root)
        └── Server Certificate (signed by intermediate)
              sip.telnyx.com
```

**Validation process:** The client receives the server's certificate and intermediate certificate(s). It validates:
1. The server certificate is signed by the intermediate CA
2. The intermediate CA is signed by the root CA
3. The root CA is in the client's **trust store** (built into the OS or application)
4. The certificate's Common Name (CN) or Subject Alternative Name (SAN) matches the hostname
5. The certificate hasn't expired
6. The certificate hasn't been revoked (checked via CRL or OCSP)

If any check fails, the connection is rejected with a TLS alert.

### Certificate Problems in NOC Operations

**Expired certificates** are the #1 TLS issue. Certificates have a validity period (typically 1-2 years, or 90 days for Let's Encrypt). When they expire, every connection fails simultaneously.

**Missing intermediate certificates:** The server must send its certificate AND the intermediate certificate(s). If the intermediate is missing, clients that don't have it cached will fail validation. This is intermittent — some clients work (cached intermediate), others don't.

**Wrong hostname:** A certificate for `sip.example.com` won't validate for connections to `sip2.example.com`. Wildcard certificates (`*.example.com`) cover subdomains but not the bare domain.

**Self-signed certificates:** Not signed by a trusted CA. Requires the client to explicitly trust them. Common in lab environments but inappropriate for production. SIP phones configured to "accept all certificates" bypass validation entirely — convenient but insecure.

🔧 **NOC Tip:** Debug certificate issues with `openssl s_client`:
```bash
openssl s_client -connect sip.telnyx.com:5061 -servername sip.telnyx.com
```
This shows the full certificate chain, expiry dates, and validation result. If the connection fails, the error message tells you exactly what's wrong: `certificate has expired`, `unable to get local issuer certificate` (missing intermediate), or `hostname mismatch`.

## Server Name Indication (SNI)

**SNI** is a TLS extension where the client includes the hostname it's connecting to in the ClientHello message (in plaintext, before encryption). This allows a server to host multiple domains on a single IP address and present the correct certificate for each.

Without SNI, a server with one IP could only serve one certificate. SNI is critical for:
- **SIP:** Multiple SIP domains on shared infrastructure
- **HTTPS:** Virtual hosting on CDNs and load balancers
- **Webhook delivery:** Connecting to customer HTTPS endpoints

**SNI and firewalls:** Because SNI is in plaintext, firewalls can see which hostname is being accessed even though the traffic is encrypted. This is used for domain-based filtering. TLS 1.3's Encrypted ClientHello (ECH) aims to fix this, but it's not yet widely deployed.

## Mutual TLS (mTLS): Client Certificates

Standard TLS authenticates only the server. **Mutual TLS** adds client authentication — the server requests a client certificate, and the client must present a valid one.

For SIP trunks, mTLS provides strong authentication:
1. Telnyx's server presents its certificate (server authentication)
2. The customer's SBC presents a client certificate (client authentication)
3. No SIP digest auth needed — the TLS layer handles identity

mTLS is more secure than digest authentication (which sends hashed credentials over potentially unencrypted SIP). It's also more operationally complex — client certificates must be issued, distributed, and renewed.

### Real Troubleshooting Scenario

**Scenario:** A customer's SIP trunk suddenly stops working. All calls fail. No SIP messages appear in the server logs at all — not even malformed ones.

**Investigation:** The TLS handshake fails before any SIP data is exchanged. Running `openssl s_client` against the customer's SBC reveals: `verify error:num=10:certificate has expired`. The customer's client certificate (used for mTLS authentication) expired at midnight.

**Fix:** The customer renews their client certificate and installs it on their SBC. Calls resume immediately.

**Prevention:** Monitor certificate expiry dates. Set alerts for 30, 14, and 7 days before expiry. Automate renewal where possible (ACME/Let's Encrypt for server certs).

🔧 **NOC Tip:** When SIP over TLS connections fail completely (no SIP traces at all), the problem is always in the TLS handshake — before SIP starts. Capture at the TCP level. Common causes: expired certificate, untrusted CA, TLS version mismatch, cipher suite mismatch, or SNI mismatch. `openssl s_client` is your best friend here.

## TLS Session Resumption

Full TLS handshakes are expensive. Session resumption allows subsequent connections to skip the certificate exchange:

- **TLS 1.2 Session Tickets:** Server sends an encrypted ticket containing session state. Client presents the ticket on reconnection.
- **TLS 1.3 0-RTT (Early Data):** Client sends application data in the first message using a pre-shared key from a previous session. The server responds immediately. This achieves **zero round trips** for resumed connections — the TLS overhead is effectively eliminated.

For persistent SIP TCP connections, session resumption matters less (the connection stays up). But for webhook delivery and API calls (many short connections), it significantly reduces latency.

---

**Key Takeaways:**
1. TLS encrypts the transport channel, providing confidentiality, integrity, and authentication — essential for SIP signaling (SIPS on port 5061) and API/webhook security
2. TLS 1.2 requires 2 round trips for handshake; TLS 1.3 reduces this to 1, with 0-RTT possible for resumed sessions
3. Certificate validation checks the trust chain (root → intermediate → server), hostname match, expiry, and revocation — any failure kills the connection
4. Expired certificates and missing intermediates are the most common TLS failures in production; use `openssl s_client` to diagnose
5. Mutual TLS (mTLS) authenticates both sides and can replace SIP digest auth for trunk authentication, but requires certificate lifecycle management

**Next: Lesson 18 — The Application Layer: HTTP, WebSockets, and gRPC**
