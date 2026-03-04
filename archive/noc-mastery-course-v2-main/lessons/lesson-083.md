# Lesson 83: Number Porting — The Complete Lifecycle
**Module 2 | Section 2.7 — Numbers**
**⏱ ~8 min read | Prerequisites: Lesson 72, Lesson 4**

---

## Why Number Porting Exists

In the early days of telephony, your phone number was tied to your carrier. Switching carriers meant getting a new number — a powerful lock-in mechanism. Regulators recognized this anti-competitive dynamic and mandated **Local Number Portability (LNP)** — the right for customers to keep their phone numbers when changing providers.

As we covered in Lesson 4, LNP relies on the Location Routing Number (LRN) system. When a number ports, the NPAC (Number Portability Administration Center) database is updated so that calls to that number are routed to the new carrier's network via the LRN. But the technical routing change is only the final step in a process that involves paperwork, verification, and coordination between carriers.

## The Port-In Process

When a Telnyx customer wants to bring their existing numbers from another carrier, they initiate a **port-in**. This process has several distinct phases:

### Phase 1: Letter of Authorization (LOA)

The customer signs an LOA — a legal document authorizing Telnyx to port their numbers away from the current carrier (the "losing carrier"). The LOA must include:

- The authorized person's name (must match the account holder at the losing carrier)
- The service address on file with the losing carrier
- The account number with the losing carrier
- The specific numbers to port
- A signature and date

Every field matters. A mismatch between the LOA and the losing carrier's Customer Service Record (CSR) will cause a rejection.

### Phase 2: CSR Verification

The **Customer Service Record (CSR)** is the losing carrier's record of the customer's account. It contains the account holder name, service address, account number, PIN (if applicable), and the numbers on the account.

Before submitting the port request, Telnyx verifies the LOA information against the CSR data. Mismatches are the #1 cause of port rejections. Common issues:

- **Name mismatch** — The customer goes by "Bob Smith" but the account is under "Robert J. Smith Inc."
- **Address mismatch** — The customer moved but never updated their carrier account
- **Account number format** — Some carriers use different account number formats for different purposes
- **PIN required** — The losing carrier requires a port-out PIN that the customer didn't provide

🔧 **NOC Tip:** When a port request is rejected, the losing carrier provides a rejection reason. Always check this reason — it usually points directly to the mismatched field. Guide the customer to obtain their CSR from the losing carrier and update the LOA accordingly.

### Phase 3: Port Request Submission

Telnyx submits the port request to the losing carrier through the industry's porting systems. In the US, this goes through the **NPAC** (managed by iconectiv). The request includes all the LOA details and the requested numbers.

Ports are classified as **simple** or **complex**:

- **Simple ports** — Single line, no special features, residential. Can complete in as little as 1 business day (regulatory minimum in the US).
- **Complex ports** — Multiple lines, PRI circuits, toll-free numbers, or lines with special features (DSL, alarm systems). These require project management and can take 1-4 weeks.

### Phase 4: FOC Date

If the losing carrier accepts the port request, they issue a **Firm Order Commitment (FOC)** date — the date and time the number will transfer. The FOC is a commitment: on this date, the losing carrier will release the number and the NPAC database will be updated to route calls to Telnyx.

The FOC date gives both carriers time to prepare. Telnyx must ensure the number is provisioned in its routing tables before the FOC date. The losing carrier must prepare to stop serving the number.

### Phase 5: The Cutover

On the FOC date, the actual port happens:

1. The losing carrier's routing for the number is deactivated
2. The NPAC database is updated with Telnyx's LRN for the number
3. Telnyx's routing becomes active
4. New calls to the number are now routed to Telnyx

This cutover isn't instantaneous across all carriers. Some carriers cache LRN data and may take minutes to hours to pick up the change. During this window, some calls might still route to the old carrier.

🔧 **NOC Tip:** If a customer reports "some calls are coming through after the port but not all," it's likely a caching issue. Different originating carriers update their LRN cache at different intervals. This typically resolves within 24-48 hours. Verify the NPAC database shows the correct LRN using a dip query.

## Common Porting Failures

### Rejection at Submission

- **CSR mismatch** (most common) — Name, address, or account number doesn't match
- **Number not portable** — Some numbers genuinely can't be ported (certain special-use numbers)
- **Outstanding balance** — Some carriers require accounts to be current before allowing port-out
- **Pending order conflict** — Another order is already in progress for the same number

### Failure at Cutover

- **Provisioning incomplete** — Telnyx's routing wasn't ready before the FOC date
- **NPAC update failure** — The database update failed (rare but serious)
- **Partial port** — Some numbers in a multi-number port succeed while others fail

### Post-Port Issues

- **Calls routing to old carrier** — LRN cache staleness (wait 24-48 hours)
- **SMS not working** — SMS routing uses different databases than voice; the messaging port may need separate processing
- **911 issues** — E911 address wasn't provisioned for the ported number at Telnyx

## Porting Timeline Expectations

| Port Type | Typical Timeline | Regulatory Minimum |
|-----------|-----------------|-------------------|
| Simple (US) | 1-3 business days | 1 business day |
| Complex (US) | 1-4 weeks | Varies |
| Toll-free (US) | 3-7 business days | N/A |
| International | 1-8 weeks | Varies by country |

International porting is significantly more complex. Each country has its own regulatory framework, porting procedures, and timelines. Some countries require in-person verification or notarized documents.

## Port-Out Obligations

When a Telnyx customer wants to leave and port their numbers to another carrier, Telnyx has **legal obligations**:

- Must not block or unreasonably delay port-out requests
- Must respond to port requests within regulatory timeframes
- Can only reject for legitimate reasons (CSR mismatch, unauthorized request)
- Cannot require contract termination fees as a condition of porting (in most jurisdictions)

The NOC may be involved in port-out issues when the gaining carrier reports problems. Verify the port request details match Telnyx's records and process accordingly.

## Real-World Troubleshooting Scenario

**Scenario:** A customer's port completed (FOC date passed), but they report no inbound calls are arriving.

**Investigation steps:**
1. **Verify NPAC** — Perform an LRN dip on the ported number. Does it return Telnyx's LRN? If not, the NPAC update may have failed.
2. **Check Telnyx routing** — Is the number provisioned in Telnyx's routing tables? Is it assigned to a connection?
3. **Test call** — Place a test call to the number from an external phone. Watch SIP traces for the call. Does the INVITE arrive at Telnyx's edge?
4. **Check the old carrier** — If the INVITE doesn't arrive at Telnyx, calls may still be routing to the old carrier. Contact them to verify they've released the number.
5. **Check SIP traces** — If the INVITE arrives but the call fails, the issue is internal routing or connection configuration (similar to any inbound call failure — see Lesson 59).

**Resolution:** If the NPAC shows the wrong LRN, escalate to the porting team to resubmit the NPAC update. If routing tables are missing the number, trigger reprovisioning. If the old carrier hasn't released, escalate through the porting dispute process.

---

**Key Takeaways:**
1. Number porting is a regulated process involving LOA, CSR verification, FOC dates, and NPAC database updates
2. CSR mismatches are the #1 cause of port rejections — always verify LOA details match the losing carrier's records exactly
3. Simple ports can complete in 1-3 days; complex and international ports can take weeks
4. Post-port call routing issues are often caused by LRN cache staleness — allow 24-48 hours for full propagation
5. SMS routing is separate from voice routing — a successful voice port doesn't automatically mean SMS works
6. Port-out is a legal obligation — Telnyx cannot unreasonably block customers from leaving

**Next: Lesson 74 — CNAM, E911, and Number Features**
