# Lesson 150: SIP Security - Toll Fraud Detection and Prevention
**Module 5 | Section 5.1 - Network Security**
**⏱ ~8 min read | Prerequisites: Lessons 50-55, 131**

---

## The Financial Threat of Toll Fraud

Toll fraud is the most financially damaging security threat to telecom platforms. Attackers exploit SIP infrastructure to make expensive international calls, generating revenue from premium-rate numbers they control. A successful toll fraud attack can cost a provider tens of thousands of dollars in a single night.

Understanding how toll fraud works is essential for NOC engineers because you'll often be the first to detect it - and detection speed directly correlates with dollar savings.

## How Toll Fraud Works

### The Basic Attack

1. **Compromise or exploit**: Attacker gains access to SIP credentials through brute force, leaked credentials, or misconfigured systems
2. **Test calls**: Attacker makes test calls to verify access and check audio quality
3. **Attack calls**: Attacker routes calls to premium-rate international destinations - countries like Cuba, Somalia, or premium-rate numbers in Eastern Europe
4. **Revenue split**: The terminating carrier shares revenue with the fraudster
5. **Detection delay**: Fraud continues until someone notices unusually high call volumes or costs

### International Revenue Share Fraud (IRSF)

The most sophisticated variant involves premium-rate numbers in specific countries. The fraudster's accomplice operates the terminating carrier, charging $0.50-$2.00 per minute. The fraudster gets a cut of this revenue - sometimes 30-50%.

Because the calls technically complete successfully, standard fraud detection that only looks at call failures misses IRSF entirely.

## Detection Patterns

Toll fraud has distinctive signatures:

### Volume Signatures
- **Off-hours spikes**: Legitimate business traffic peaks during business hours; fraud often occurs at night or weekends
- **Unusual destinations**: Calls to countries the customer never calls
- **Short duration calls**: Fraudsters often make many short calls rather than fewer long ones to avoid detection
- **Rapid dial rate**: Hundreds of calls per minute from a single trunk

### Destination Signatures
- **High-cost countries**: Cuba, Somalia, Gambia, Latvia premium numbers
- **Known fraud destinations**: Lists of premium numbers associated with fraud
- **Geographic anomalies**: A US customer suddenly making calls to obscure international destinations

🔧 **NOC Tip:** Maintain a list of high-risk destination countries and premium number blocks. Create Grafana dashboards showing call volume to these destinations. Any spike should trigger immediate investigation.

## Detection Metrics in Grafana

```promql
# Calls per destination country per hour
sum by (country_code) (rate(calls_total[1h]))

# Cost per customer per hour (if billing data available)
sum by (customer_id) (increase(call_cost_total[1h]))

# Unusual destinations for a customer
topk(10, sum by (destination) (rate(calls_total{customer_id="specific"}[1h])))

# Off-hours call volume (should be near zero for business customers)
sum(rate(calls_total[5m])) and on() hour() < 6 or hour() > 20
```

## Prevention Strategies

### Authentication Controls
- **Strong credentials**: Require complex passwords for SIP authentication
- **IP whitelisting**: Only allow SIP from known customer IP addresses
- **Certificate-based auth**: Mutual TLS instead of password auth

### Rate Limiting
- **CPS limits per trunk**: Maximum calls per second per customer
- **Concurrent call limits**: Maximum simultaneous calls per trunk
- **Destination-based limits**: Stricter limits to international destinations
- **Cost-based limits**: Daily/hourly spend caps that block calls when exceeded

### Fraud Detection Rules
1. **No international calling by default**: Require explicit enablement
2. **High-cost destination whitelisting**: Explicit approval for premium routes
3. **Off-hours blocking**: Block or rate-limit international calls outside business hours
4. **Geo-IP correlation**: Flag calls from IP addresses in different countries than the customer's billing address

## Real-World Scenario: The Weekend Horror

**Saturday, 2:00 AM**: A toll fraud alert fires - a customer with a typical monthly bill of $500 has accumulated $3,200 in charges in the last 4 hours.

**Investigation:**
- Customer normally makes domestic calls only
- Last 4 hours: 847 calls to premium numbers in Cuba
- Call pattern: 20-30 second calls, rapid succession, SIP credentials used from an IP in Eastern Europe

**Response:**
1. **Immediate**: Block all international calling on the customer's trunk
2. **Forensics**: Review how credentials were compromised (likely brute-force over several days)
3. **Customer notification**: Call customer, explain situation, recommend credential reset
4. **Refund discussion**: Work with billing on potential goodwill credits
5. **Prevention**: Enable IP whitelisting for the customer, recommend credential complexity

**Cost**: $3,200 in fraudulent charges. Quick detection limited what could have been $20,000+ over a weekend.

🔧 **NOC Tip:** Set alerts on cost-per-customer metrics, not just call volume. A low-volume attack to premium destinations can rack up thousands in charges while appearing normal in call count charts.

## Fraud Monitoring Dashboard

Essential panels:

1. **Top 10 spenders (last hour)**: Who's accumulating charges fastest
2. **International calls by customer**: Flag customers who don't normally call internationally
3. **Off-hours activity**: Calls during 2-6 AM local time
4. **Failed authentication rate**: High REGISTER failure rates suggest brute-force attacks
5. **New destination alerts**: First-time calls to premium destinations

## When You Suspect Fraud

1. **Don't panic-block immediately** - verify it's not legitimate heavy usage
2. **Check customer profile**: Is this an international calling customer or domestic-only?
3. **Check source IP**: Geographic anomalies are a strong signal
4. **Check call patterns**: Numerous short calls to same destination is suspicious
5. **Coordinate with customer**: Confirm they're intentionally making these calls

If confirmed fraud:
1. Block the trunk's international access immediately
2. Reset credentials and recommend IP whitelisting
3. Document for post-mortem and billing review
4. Review if detection was fast enough - adjust thresholds if needed

---

**Key Takeaways:**
1. Toll fraud is the most financially damaging telecom security threat - detection speed equals dollar savings
2. Fraud operators route calls to premium-rate destinations in specific countries for revenue sharing
3. Detection relies on identifying anomalies: off-hours spikes, unusual destinations, rapid dial rates
4. Prevention combines strong authentication, rate limiting, destination controls, and geo-IP correlation
5. Monitor cost-per-customer metrics, not just call volume - premium destinations look normal by count
6. When investigating suspected fraud, verify customer intent before blocking to avoid false positives

**Next: Lesson 135 - SIP Registration Attacks and Overs Detection**
