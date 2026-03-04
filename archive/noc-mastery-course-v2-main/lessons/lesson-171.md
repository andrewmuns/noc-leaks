# Lesson 171: Database Backup and Recovery Procedures
**Module 5 | Section 5.3 — Databases for NOC**
**⏱ ~6 min read | Prerequisites: Lesson 154**

---

## The Last Line of Defense

Replication (Lesson 154) protects against hardware failures — if a server dies, a replica takes over. But replication doesn't protect against **data corruption**, **accidental deletion**, or **software bugs that write bad data**. A corrupted table or an accidental `DELETE FROM customers WHERE ...` (without a proper WHERE clause) replicates instantly to all replicas. Within seconds, every copy of your database has the same corruption.

Backups are your time machine. They let you rewind to a point before the disaster happened. For a telecom platform, the difference between having tested backups and not can be the difference between a 30-minute recovery and a total data loss event.

## Backup Types

### Logical Backups: pg_dump

`pg_dump` exports database contents as SQL statements or a custom binary format. It's like taking a photograph of your data.

```bash
# Dump a single database to compressed custom format
pg_dump -h replica-host -Fc -f telecom_backup.dump telecom_production

# Dump specific tables
pg_dump -h replica-host -Fc -t cdrs -t customers -f partial_backup.dump telecom_production

# Restore from dump
pg_restore -h new-host -d telecom_production telecom_backup.dump
```

**Advantages:**
- Portable — can restore to different PostgreSQL versions
- Selective — dump/restore individual tables
- Readable — SQL format can be inspected

**Disadvantages:**
- Slow for large databases (serializes all data)
- Restoration rebuilds indexes from scratch (very slow)
- No point-in-time recovery

🔧 **NOC Tip:** Always run `pg_dump` against a **replica**, never the primary. Dumping takes a shared lock and generates significant I/O, which can impact production performance.

### Physical Backups: pg_basebackup

`pg_basebackup` copies the entire PostgreSQL data directory — a binary-level copy of every file.

```bash
# Full base backup with WAL included
pg_basebackup -h primary-host -D /backups/base_20240115 \
    --checkpoint=fast --wal-method=stream -P
```

**Advantages:**
- Fast — copies files directly, no serialization
- Complete — captures the entire cluster
- Enables Point-in-Time Recovery (PITR) when combined with WAL archiving

**Disadvantages:**
- Not portable across PostgreSQL major versions
- Cannot selectively restore individual tables
- Large — copies the full data directory

## Point-in-Time Recovery (PITR)

PITR is the gold standard for database recovery. It combines a base backup with WAL archives to restore the database to **any specific moment in time**.

The concept:
1. Take a base backup daily (e.g., at 02:00)
2. Continuously archive WAL files to object storage (S3, GCS)
3. To recover: restore the base backup, then replay WAL files up to the desired point

```
Base Backup (02:00)  +  WAL Archives (02:00 → 14:37)  =  Database at 14:37
```

If someone accidentally deletes a table at 14:38, you restore to 14:37 — one minute before the disaster.

### WAL Archiving Configuration

```ini
# postgresql.conf
archive_mode = on
archive_command = 'aws s3 cp %p s3://db-backups/wal/%f'
```

Every completed WAL segment (16 MB by default) is copied to S3. Combined with a daily base backup, this gives you PITR capability with a granularity of individual transactions.

### Performing PITR

```bash
# 1. Stop PostgreSQL
# 2. Restore base backup
cp -r /backups/base_20240115/ /var/lib/postgresql/data/

# 3. Create recovery configuration
cat > /var/lib/postgresql/data/recovery.signal << EOF
EOF

# 4. Configure recovery target in postgresql.conf
echo "restore_command = 'aws s3 cp s3://db-backups/wal/%f %p'" >> postgresql.conf
echo "recovery_target_time = '2024-01-15 14:37:00 UTC'" >> postgresql.conf

# 5. Start PostgreSQL — it replays WAL up to the target time
```

🔧 **NOC Tip:** Know your **RPO** (Recovery Point Objective) and **RTO** (Recovery Time Objective) for each database. RPO is how much data you can afford to lose (with WAL archiving, it's typically seconds). RTO is how long recovery can take (PITR of a 500 GB database might take 2-4 hours). These numbers must be documented and tested.

## Backup Tools: pgBackRest and WAL-G

Manual `pg_basebackup` + WAL archiving works but is fragile. Production environments use dedicated backup tools:

### pgBackRest
- Parallel backup and restore (much faster)
- Incremental backups (only changed files)
- Backup verification and integrity checks
- Backup retention policies

### WAL-G
- Lightweight WAL archiver and backup tool
- Designed for cloud storage (S3, GCS, Azure)
- Delta backups (block-level changes)
- Used extensively in Kubernetes PostgreSQL deployments

```bash
# pgBackRest: take an incremental backup
pgbackrest --stanza=main backup --type=incr

# pgBackRest: list backups
pgbackrest --stanza=main info

# pgBackRest: restore to a point in time
pgbackrest --stanza=main restore --target='2024-01-15 14:37:00+00' --type=time
```

## The Golden Rule: Test Your Restores

A backup that hasn't been tested is not a backup — it's a hope.

**Backup verification schedule:**
- **Weekly:** Automated restore test to a staging environment
- **Monthly:** Full PITR test — restore to a random point in time, verify data integrity
- **Quarterly:** Full disaster recovery drill — simulate complete primary loss, measure actual RTO

```bash
# Automated restore verification script
#!/bin/bash
pg_restore -h test-server -d test_db /backups/latest.dump
if [ $? -eq 0 ]; then
    psql -h test-server -d test_db -c "SELECT count(*) FROM customers;" > /dev/null
    echo "Backup verification: PASSED"
else
    echo "Backup verification: FAILED - ALERT!"
    # Send PagerDuty alert
fi
```

### A Real Disaster Scenario

**Incident:** An engineer runs a migration script in production instead of staging. The script drops and recreates a table, losing all customer routing configurations.

**Timeline:**
- 14:38 — Script executed accidentally
- 14:39 — Routing failures spike (customers can't be looked up)
- 14:40 — NOC alerts fire
- 14:42 — Engineer realizes the mistake
- 14:45 — Decision: PITR to 14:37
- 14:50 — Base backup restoration begins
- 16:20 — WAL replay completes (1.5 hours for a 200 GB database)
- 16:25 — Verification: data intact, routing restored
- 16:30 — Service fully recovered

**Total outage: ~2 hours.** Without backups? Unrecoverable. The routing data would need to be manually recreated from scattered sources — days of work and customer impact.

## Backup Monitoring for NOC

Add these to your monitoring:

| Check | Frequency | Alert Threshold |
|-------|-----------|-----------------|
| Last successful backup | Every hour | > 26 hours ago |
| WAL archiving status | Every 5 min | Archive lag > 100 segments |
| Backup size trend | Daily | > 20% deviation from trend |
| Restore test result | Weekly | Any failure |
| Backup storage utilization | Daily | > 80% capacity |

```sql
-- Check WAL archiving status on primary
SELECT archived_count, failed_count,
       last_archived_wal, last_archived_time
FROM pg_stat_archiver;
```

If `failed_count` is increasing, WAL archiving is broken — your PITR capability is degrading every minute.

---

**Key Takeaways:**
1. Replication protects against hardware failure; backups protect against data corruption and human error
2. pg_dump is for selective, portable backups; pg_basebackup + WAL archiving enables point-in-time recovery
3. PITR lets you restore to any specific moment — the gold standard for disaster recovery
4. Know your RPO and RTO for every critical database and test them regularly
5. A backup that hasn't been restored in a test is not a backup — verify weekly
6. Monitor WAL archiving health continuously — broken archiving means degrading recovery capability

**Next: Lesson 156 — Shell Scripting Fundamentals for NOC**
