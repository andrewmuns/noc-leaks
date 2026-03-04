# Lesson 89: eSIM — QR Provisioning and Remote Profile Management
**Module 2 | Section 2.10 — IoT/Wireless**
**⏱ ~5 min read | Prerequisites: Lesson 78**

---

## The Physical SIM Problem

Traditional SIM cards have a fundamental limitation: they're physical objects. Deploying 10,000 IoT sensors means handling 10,000 tiny plastic cards — ordering, shipping, inserting, and potentially replacing them if a carrier change is needed. For consumer devices, it means visiting a store or waiting for mail. The eSIM (embedded SIM) eliminates this friction.

## eSIM vs. Physical SIM

An eSIM is a **reprogrammable SIM chip soldered directly into the device**. It contains the same secure element as a physical SIM (IMSI, Ki, authentication functions) but with one crucial difference: its profile can be changed remotely.

| Feature | Physical SIM | eSIM |
|---------|-------------|------|
| Form factor | Removable card | Soldered chip |
| Profile changes | Swap the card | Remote download |
| Multi-profile | One profile at a time | Multiple profiles stored |
| Carrier switch | New card needed | Download new profile |
| Manufacturing | Insert during assembly | Solder during manufacturing |

The hardware standard is **eUICC** (embedded Universal Integrated Circuit Card) — a chip that can securely store and switch between multiple operator profiles.

## GSMA RSP Architecture

The GSMA (the mobile industry's trade body) defined the **Remote SIM Provisioning (RSP)** architecture that makes eSIM work. Understanding this architecture is essential for troubleshooting provisioning failures.

### Key Components

**SM-DP+ (Subscription Manager - Data Preparation Plus)** — The server that prepares and hosts SIM profiles. Think of it as a "profile store." When a customer orders an eSIM profile from Telnyx, the profile is created and stored on the SM-DP+.

**SM-DS (Subscription Manager - Discovery Server)** — An optional server that helps devices discover which SM-DP+ has a profile waiting for them. Not always used — QR codes bypass this by encoding the SM-DP+ address directly.

**LPA (Local Profile Assistant)** — Software running on the device that manages the eSIM. It communicates with the SM-DP+ to download profiles and with the eUICC to install them.

**eUICC** — The eSIM chip itself. It securely stores profiles and handles the cryptographic operations for authentication.

## QR Code Provisioning Flow

The most common eSIM provisioning method uses QR codes:

1. **Profile creation** — Telnyx creates an eSIM profile on the SM-DP+ (containing IMSI, Ki, network credentials, APN settings)
2. **QR code generation** — A QR code is generated containing the SM-DP+ address and an activation code. The QR code encodes a string like: `LPA:1$smdp.telnyx.com$ACTIVATION_CODE`
3. **User scans QR code** — The device's LPA reads the QR code
4. **Profile download** — The LPA connects to the SM-DP+ using the activation code and downloads the profile over a secure TLS connection
5. **Profile installation** — The LPA installs the profile into the eUICC
6. **Profile activation** — The profile is enabled and the device registers on the cellular network

🔧 **NOC Tip:** QR provisioning failures usually occur at step 4 (download). Common causes: the device has no internet connectivity to reach the SM-DP+ (chicken-and-egg problem — needs connectivity to download the profile that gives it connectivity), the activation code has expired, or TLS certificate issues prevent the secure connection. Ensure the device has WiFi or an existing cellular connection before scanning.

## Profile Management

Once installed, profiles can be managed remotely:

### Install
Download and install a new profile from the SM-DP+. A device can store multiple profiles simultaneously (typically 5-10, depending on the eUICC's memory).

### Enable / Disable
Only one profile can be active at a time (on most implementations). Enabling a new profile automatically disables the current one. This is how carrier switching works — the device has profiles from multiple carriers and switches between them.

### Delete
Remove a profile from the eUICC, freeing memory for new profiles. Deleted profiles must be re-downloaded from the SM-DP+ if needed again.

### The Bootstrap Profile
Some eSIM devices ship with a **bootstrap profile** — a minimal profile that provides basic connectivity (enough to download a full profile). This solves the chicken-and-egg problem: the device can connect to a cellular network using the bootstrap profile, then download the operator's full profile.

## IoT eSIM vs. Consumer eSIM

The GSMA defines two RSP specifications:

**M2M (Machine-to-Machine)** — Designed for IoT devices that are managed by a single entity. Profile management is server-driven (the operator pushes profile changes). Devices don't have a user interface for QR scanning.

**Consumer** — Designed for phones and tablets. Profile management is user-driven (the user scans a QR code or browses a profile catalog). Requires a user interface.

Telnyx's IoT eSIM offering primarily uses the M2M specification, where profiles are managed programmatically via API rather than requiring user interaction.

## eSIM at Telnyx

Telnyx's eSIM product provides:

- **API-driven profile management** — Create, activate, suspend, and delete eSIM profiles programmatically
- **Multi-IMSI profiles** — A single eSIM profile that contains multiple IMSIs, allowing the device to present different identities to different networks (optimizing roaming)
- **Global connectivity** — eSIM profiles that work across hundreds of carriers worldwide
- **Fleet management** — Bulk operations for managing thousands of eSIM-enabled devices

## Real-World Troubleshooting Scenario

**Scenario:** A customer deploys 200 IoT devices with Telnyx eSIM. 180 provision successfully, but 20 fail during QR code scanning with "unable to connect to server."

**Investigation:**
1. **Check SM-DP+ availability** — Is the SM-DP+ server reachable? Check service health monitoring.
2. **Check activation codes** — Have the codes for the failed devices expired? Activation codes have a validity window.
3. **Check device connectivity** — Do the failing devices have internet access to reach the SM-DP+? They need WiFi or a bootstrap cellular connection.
4. **Check TLS** — The LPA connects to the SM-DP+ over TLS. If the device's clock is wrong (common in new IoT devices that haven't synced NTP), TLS certificate validation fails.
5. **Check eUICC compatibility** — Some older eUICC chips may not support newer profile formats.

**Resolution:** For clock-related TLS failures, ensure devices sync NTP before eSIM provisioning. For expired activation codes, generate new ones. For connectivity issues, ensure a bootstrap profile or WiFi is available. For eUICC compatibility, verify the profile format matches the chip's capabilities.

---

**Key Takeaways:**
1. eSIM replaces physical SIM cards with a reprogrammable chip (eUICC) that can store multiple operator profiles
2. The GSMA RSP architecture (SM-DP+, SM-DS, LPA, eUICC) governs how profiles are created, distributed, and managed
3. QR code provisioning encodes the SM-DP+ address and activation code — the device downloads the profile over TLS
4. The chicken-and-egg problem (need connectivity to download the profile that provides connectivity) is solved by bootstrap profiles or WiFi
5. IoT eSIM uses M2M RSP (server-driven management), while consumer eSIM is user-driven (QR codes, profile catalogs)

**Next: Lesson 80 — Telnyx Networking — Cloud VPN and WireGuard**
