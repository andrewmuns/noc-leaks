# Lesson 88: IoT/Wireless — SIM Provisioning and Data Sessions
**Module 2 | Section 2.10 — IoT/Wireless**
**⏱ ~7 min read | Prerequisites: Lesson 13**

---

## Telnyx as a Mobile Operator

Telnyx isn't just a VoIP company — it's also a mobile virtual network operator (MVNO) providing cellular connectivity for IoT devices. This means SIM cards, data sessions, roaming agreements, and a completely different protocol stack from the SIP/RTP world we've been studying. For NOC engineers, IoT/wireless issues require a different mental model.

## SIM Fundamentals

A **SIM (Subscriber Identity Module)** is a secure element that stores:

- **IMSI** (International Mobile Subscriber Identity) — The subscriber's unique identifier on the mobile network. Think of it as the "phone number" of the cellular world, except it identifies the subscription, not the person.
- **Ki** (Authentication Key) — A 128-bit secret key used for mutual authentication between the SIM and the network. This key never leaves the SIM — authentication is done via challenge-response.
- **ICCID** (Integrated Circuit Card Identifier) — The SIM card's serial number. This is what you see printed on the physical card.
- **MSISDN** — The phone number associated with the SIM (though many IoT SIMs don't have a voice-capable number).

The SIM's authentication mechanism is remarkably similar to SIP digest authentication (Lesson 43): the network sends a challenge, the SIM computes a response using its secret key, and the network verifies it. The crucial difference is that the SIM's key is stored in tamper-resistant hardware, making it far more secure.

## SIM Lifecycle

### Ordering

Telnyx customers order SIM cards through the portal or API. Each SIM ships with a pre-provisioned ICCID and IMSI. Bulk orders are common for IoT deployments — a fleet management company might order 10,000 SIMs at once.

### Activation

A SIM starts in an **inactive** state. Activation can happen:
- **On first use** — The SIM activates when it first connects to a cellular network
- **Via API** — The customer explicitly activates the SIM through Telnyx's API
- **Bulk activation** — Multiple SIMs activated simultaneously for fleet deployments

### Active States

Once active, a SIM can be in several states:
- **Active** — Normal operation, can connect to networks
- **Suspended** — Temporarily disabled (e.g., customer paused the subscription). No data connectivity but the SIM retains its configuration.
- **Disabled** — Permanently deactivated. Cannot be reactivated.

🔧 **NOC Tip:** When a customer reports "my IoT device can't connect," the first check is SIM status. A surprising number of connectivity issues are simply suspended or inactive SIMs. Check the SIM status via the API before investigating network-level issues.

## APN: The Gateway to Data

The **APN (Access Point Name)** is the gateway between the cellular network and external data networks (like the internet). When a device establishes a data session, it specifies which APN to connect to. The APN determines:

- **Network routing** — Where data traffic is routed (public internet, private VPN, Telnyx's backbone)
- **IP addressing** — What IP address the device receives (public or private)
- **Authentication** — Whether additional credentials are required beyond SIM authentication
- **QoS** — Traffic priority and bandwidth limits

Telnyx provides a default APN for general internet connectivity, and customers can configure custom APNs for private networking scenarios (connecting IoT devices directly to their private infrastructure without traversing the public internet).

### Data Session Establishment

When an IoT device powers on and needs data:

1. **Attach** — The device authenticates with the cellular network using the SIM's credentials
2. **PDP Context / PDN Connection** — The device requests a data session, specifying the APN
3. **IP Assignment** — The network assigns an IP address to the device
4. **Bearer Setup** — A data bearer is established with specific QoS parameters
5. **Data flows** — The device can now send and receive IP traffic

This process is managed by the cellular core network (EPC in 4G, 5GC in 5G). Telnyx's mobile core handles session management, IP assignment, and routing.

🔧 **NOC Tip:** Data session failures often come down to APN configuration. If a device can authenticate (attach) but can't get data, check the APN settings on the device. A mistyped APN name is one of the most common IoT connectivity issues.

## Data Session Management via API

Telnyx's API provides programmatic control over data sessions:

- **List active sessions** — See which SIMs have active data connections
- **Monitor usage** — Real-time data consumption tracking
- **Set data limits** — Cap data usage per SIM or per billing period
- **Force disconnect** — Terminate a data session remotely

This API-driven approach is essential for IoT fleet management. A customer managing thousands of sensor devices needs programmatic tools, not manual intervention.

## OTA: Over-the-Air Management

**OTA (Over-the-Air)** management allows remote updates to SIM configuration without physical access:

- **Profile updates** — Change the SIM's network configuration, APN settings, or security parameters
- **IMSI swaps** — Change the subscriber identity (useful for switching between carrier profiles)
- **Applet installation** — Load small applications onto the SIM's secure element

OTA uses SMS as its transport — binary SMS messages carry OTA commands to the SIM. This is transparent to the user and device application.

## Roaming: How IoT Devices Work Globally

IoT devices often need to operate across countries — a shipping container with a GPS tracker travels from China to Germany to the US. Roaming makes this possible:

1. **Home network** — Telnyx (through its roaming partners) is the "home" network
2. **Visited network** — The local carrier in whatever country the device is currently in
3. **Roaming agreement** — Telnyx has agreements with carriers worldwide allowing Telnyx SIMs to connect to their networks
4. **Steering of Roaming (SoR)** — Telnyx can configure which carriers a SIM should prefer in each country (choosing the cheapest or highest-quality option)

### TAP Files: Roaming Settlement

When a Telnyx SIM uses a foreign carrier's network, that carrier needs to be paid. This is handled through **TAP (Transferred Account Procedure)** files:

- TAP files are batch records of roaming usage exchanged between carriers
- They contain detailed call/data records: SIM identity, duration, data volume, timestamps
- Settlement happens periodically (typically monthly) based on TAP file reconciliation
- Discrepancies in TAP files cause billing disputes between carriers

🔧 **NOC Tip:** If a customer reports unexpected roaming charges, check which carrier the SIM connected to. Steering of Roaming preferences might not be configured, causing the device to roam on expensive carriers. Also check if the device's data usage aligns with TAP records — discrepancies indicate billing pipeline issues.

## Real-World Troubleshooting Scenario

**Scenario:** A fleet of 500 IoT sensors deployed across multiple US states. 50 devices suddenly lose connectivity.

**Investigation:**
1. **Check SIM status** — Are the affected SIMs still active? Bulk suspension from a billing issue would affect multiple SIMs simultaneously.
2. **Geographic correlation** — Are the affected devices in the same region? A carrier outage in one area would affect devices roaming on that carrier.
3. **Check the carrier** — Which cellular carrier are these devices connected to? Check if that carrier has a reported outage.
4. **Check data sessions** — Do the devices have active PDP contexts? If they attached but have no data session, the APN configuration or core network may be the issue.
5. **Check data limits** — Did the devices hit their monthly data cap? Usage-based disconnection would affect heavy-usage devices first.

**Resolution:** If a regional carrier outage, wait for carrier resolution or implement SoR to steer devices to an alternate carrier. If billing-related suspension, resolve the billing issue and reactivate SIMs. If data cap, increase limits or help the customer optimize device data usage.

---

**Key Takeaways:**
1. SIM cards store subscriber identity (IMSI) and authentication keys (Ki) — authentication works via challenge-response, similar to SIP digest auth
2. The SIM lifecycle (inactive → active → suspended → disabled) is the first thing to check for connectivity issues
3. APN configuration determines how data traffic is routed — misconfigured APNs are a top cause of "device can't get data"
4. Roaming enables global IoT connectivity through carrier agreements, with TAP files handling inter-carrier settlement
5. API-driven SIM management is essential for IoT fleet operations at scale

**Next: Lesson 79 — eSIM — QR Provisioning and Remote Profile Management**
