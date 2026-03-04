# Lesson 69: Short Codes and High-Throughput Messaging

**Module 1 | Section 1.17 — Messaging**
**⏱ ~5min read | Prerequisites: Lesson 183 (10DLC Registration)**

---

## Introduction

When 10DLC throughput isn't enough, businesses turn to **short codes** — 5-6 digit numbers designed for high-volume A2P messaging. Short codes can deliver 100+ messages per second (MPS), making them essential for time-sensitive use cases like 2FA, emergency alerts, and large-scale marketing campaigns.

---

## Short Codes vs Long Codes

```
                    Long Code (10DLC)      Short Code
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Format:             +15551234567           72345
Digits:             10                     5-6
Throughput:         0.2-75 MPS             100-500+ MPS
Setup time:         Minutes                8-12 weeks
Monthly cost:       ~$1/number             $500-$1,500/month
Two-way:            Yes                    Yes
MMS support:        Yes                    Yes (dedicated only)
Carrier approval:   10DLC registration     Full carrier review
Shared option:      No                     Yes (keyword-based)
```

---

## Shared vs Dedicated Short Codes

### Shared Short Codes

Multiple businesses share a single short code, differentiated by **keywords**:

```
Short Code: 72345
  "PIZZA" → Routes to Pizza Co
  "BANK"  → Routes to First Bank
  "VOTE"  → Routes to Survey Corp
```

**Limitations:**
- Restricted to keyword-triggered interactions
- One bad actor can get the entire short code blocked
- Limited customization
- Being phased out by carriers (T-Mobile deprecated shared codes in 2021)

### Dedicated Short Codes

One business owns the entire short code:

```
Short Code: 55123 → All traffic belongs to Acme Corp
  Any keyword works
  Full control over content
  MMS support
  Custom opt-in/opt-out flows
```

🔧 **NOC Tip:** If a customer asks about shared short codes, steer them toward dedicated codes or toll-free numbers. Major carriers are actively deprecating shared short codes. Telnyx primarily supports dedicated short codes.

---

## Short Code Provisioning Process

### Timeline

```
Week 1-2:   Application submitted to carriers
Week 2-4:   T-Mobile review
Week 4-8:   AT&T review  
Week 6-10:  Verizon review
Week 8-12:  All carriers approved, short code live

Total: 8-12 weeks (sometimes longer)
```

### What Carriers Review

```
✓ Business identity and legitimacy
✓ Use case description and message samples
✓ Opt-in mechanism (must be explicit)
✓ Opt-out handling (STOP must always work)
✓ HELP response content
✓ Privacy policy URL
✓ Terms of service URL
✓ Message frequency disclosure
✓ Content compliance (no SHAFT content)
```

### Telnyx Short Code Setup

```bash
# Step 1: Order a short code through Telnyx
curl -X POST https://api.telnyx.com/v2/short_codes/requests \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "short_code": "55123",
    "type": "dedicated",
    "use_case": "Two-factor authentication codes",
    "sample_messages": [
      "Your Acme verification code is 847293. Valid for 5 minutes.",
      "Acme Security Alert: New login detected. Reply YES to confirm."
    ],
    "opt_in_description": "Users enter phone number during account registration",
    "message_frequency": "Up to 10 messages per month",
    "help_message": "Acme 2FA Service. Contact support@acme.com. Msg&Data rates apply.",
    "opt_out_message": "You have been unsubscribed. No more messages will be sent."
  }'
```

🔧 **NOC Tip:** Short code applications get rejected most often for vague opt-in descriptions. "Users sign up on our website" isn't specific enough. Carriers want: "Users enter their phone number and check a consent checkbox on https://acme.com/register that states 'I agree to receive SMS verification codes.'"

---

## Throughput and Rate Limits

### Typical Short Code Throughput

```
Standard dedicated short code:  100 MPS
High-volume approved:           200-500 MPS
Peak (carrier-negotiated):      500+ MPS
```

### Throughput Management

```
Telnyx queues messages and delivers at carrier-approved rate:

Customer sends 10,000 messages via API (burst)
  → Telnyx queues all 10,000
  → Delivers at 100 MPS to carrier
  → All messages delivered within ~100 seconds
  → DLR webhooks stream back as carriers confirm
```

🔧 **NOC Tip:** If a customer reports "messages sent but delivery is slow," check if they're exceeding their short code's approved MPS. Messages queue and deliver sequentially — a burst of 50,000 messages at 100 MPS takes ~8 minutes to clear the queue.

---

## Use Cases

### Two-Factor Authentication (2FA)

```
Throughput needed: 50-200 MPS (peak)
Time sensitivity: Critical (codes expire in 30-60 seconds)
Pattern: Bursty (login peaks in morning)
```

### Alerts and Notifications

```
Throughput needed: 100-500 MPS
Time sensitivity: High (emergency alerts, delivery notifications)
Pattern: Event-driven bursts
Example: "WEATHER ALERT: Tornado warning for your area until 5:00 PM"
```

### Marketing Campaigns

```
Throughput needed: 100+ MPS
Time sensitivity: Moderate (promotional, time-windowed)
Pattern: Scheduled large sends
Example: "Flash Sale! 50% off everything today. Shop now: https://acme.com/sale"
```

---

## CTIA Compliance

The **CTIA (Cellular Telecommunications Industry Association)** sets messaging best practices that carriers enforce:

### Required Program Elements

```
1. Opt-in:  Must be explicit and documented
            "Text START to 55123 to subscribe"
            
2. Opt-out: STOP keyword must always work
            Response: "You have been unsubscribed from Acme Alerts."
            
3. HELP:    Must return program information
            Response: "Acme Alerts: 10 msgs/mo. Msg&Data rates apply. 
                       Reply STOP to cancel. Help: support@acme.com"

4. Terms:   Must include in initial opt-in:
            - Program name
            - Message frequency
            - "Message and data rates may apply"
            - Opt-out instructions
            - Privacy policy link
```

### Opt-In / Opt-Out Management

```python
# Handling inbound keywords on your short code

def handle_inbound(message):
    text = message['text'].strip().upper()
    from_number = message['from']['phone_number']
    
    if text in ['STOP', 'UNSUBSCRIBE', 'CANCEL', 'END', 'QUIT']:
        unsubscribe(from_number)
        send_response(from_number, 
            "You have been unsubscribed. No more messages will be sent.")
    
    elif text in ['HELP', 'INFO']:
        send_response(from_number,
            "Acme Alerts: Up to 10 msgs/mo. Msg&Data rates apply. "
            "Reply STOP to cancel. Help: support@acme.com")
    
    elif text in ['START', 'SUBSCRIBE', 'YES']:
        subscribe(from_number)
        send_response(from_number,
            "Welcome to Acme Alerts! You'll receive up to 10 msgs/mo. "
            "Msg&Data rates apply. Reply HELP for help, STOP to cancel.")
```

🔧 **NOC Tip:** Carriers will **immediately suspend** a short code if STOP doesn't work. If you see a short code suspension, the first thing to check is whether opt-out handling is functional. Test it yourself by texting STOP to the code.

---

## Real-World NOC Scenario

**Scenario:** Customer's short code 55123 suddenly stops delivering to Verizon. T-Mobile and AT&T still work.

**Investigation:**

1. Check Telnyx short code status — is it active on all carriers?
2. Check for Verizon compliance notifications — did they flag content?
3. Review recent message content — any changes in messaging patterns?
4. Check if opt-out rate spiked (indicates unwanted messages)
5. Contact Verizon NOC through Telnyx carrier team for suspension details

```bash
# Check short code carrier status
curl https://api.telnyx.com/v2/short_codes/55123

# Review recent DLR stats by carrier
curl "https://api.telnyx.com/v2/messages?filter[from]=55123&filter[status]=failed"
```

**Common causes:** Content policy violation, broken opt-out handling, or a spike in consumer complaints.

---

## Key Takeaways

1. **Short codes deliver 100-500+ MPS** — orders of magnitude faster than 10DLC long codes
2. **Dedicated short codes** are the standard; shared codes are being deprecated
3. **Provisioning takes 8-12 weeks** — plan ahead for customer onboarding
4. **CTIA compliance is non-negotiable** — STOP must always work, HELP must respond, opt-in must be explicit
5. **Carrier-by-carrier approval** means one carrier can block while others work fine
6. **Cost is $500-$1,500/month** — justified for high-volume, time-sensitive use cases
7. **Queue math matters** — 50,000 messages at 100 MPS = 8+ minutes; set customer expectations

---

**Next: Lesson 185 — RCS: Rich Communication Services**
