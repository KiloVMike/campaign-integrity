# Sample Data

**Illustrative fixtures for the walkthrough**

These are the identifiers, hashes, and timestamps used consistently across the submission. They are not captured from a running system.

**Identifier note:** The readable IDs (`CMP-1042`, `REV-1042-1`, `DEC-9001`, `SCH-7001`) are stable aliases used for readability. In the schema, primary keys are UUIDs; each alias maps to one UUID. API paths and payloads use the aliases as placeholders.

---

## Users

| ID | Name | Role | Email |
|---|---|---|---|
| `USR-MKT-1` | Meera Kulkarni | `MARKETER` | meera@saffron.example |
| `USR-REV-1` | Arjun Rao | `REVIEWER` | arjun@saffron.example |
| `USR-REV-2` | Priya Shah | `REVIEWER` | priya@saffron.example |

The `.example` domain is reserved for documentation; no real email is used.

---

## Campaign

| Field | Value |
|---|---|
| `id` | `CMP-1042` |
| `name` | Diwali Reset |
| `created_by` | `USR-MKT-1` |
| `current_revision_id` | `REV-1042-4` |
| `created_at` | 2026-11-01 10:15 IST |
| `updated_at` | 2026-11-01 11:26 IST |

---

## Revisions

| ID | # | Objective | Audience | Channel | Budget (paise) | Hash | State | Created | Submitted |
|---|---|---|---|---|---|---|---|---|---|
| `REV-1042-1` | 1 | Win back lapsed customers with a festive bundle | All customers in India, 18–55 | `INSTAGRAM` | 50,000,000 | `H1` | `SUPERSEDED` | 10:15 | 10:22 |
| `REV-1042-2` | 2 | Win back lapsed customers with a ₹499 festive bundle | Lapsed customers in Mumbai and Pune, 25–40 | `INSTAGRAM` | 50,000,000 | `H2` | `SUPERSEDED` | 10:45 | 10:47 |
| `REV-1042-3` | 3 | Win back lapsed customers with a ₹499 festive bundle | Lapsed customers in Mumbai and Pune, 25–40 | `INSTAGRAM` | 80,000,000 | `H3` | `SUPERSEDED` | 11:20 | 11:22 |
| `REV-1042-4` | 4 | Win back lapsed customers with a ₹499 festive bundle | Lapsed customers in Mumbai, Pune, and Bangalore, 25–40 | `INSTAGRAM` | 80,000,000 | `H4` | `APPROVED` | 11:26 | 11:30 |

### Full hashes

```
H1 = 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b
H2 = 4b1d0c7a9e2f8a6c3d5e1f0b7c9a2d4e6f8b1c3d5e7a9f0b2c4d6e8f1a3b5c7d
H3 = 7f6e5d4c3b2a1908f7e6d5c4b3a29180f6e5d4c3b2a1908f7e6d5c4b3a291807
H4 = c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4
```

Each is 64 lowercase hex characters, the output of SHA-256 over the canonical JSON in [`03-low-level-design.md`](../03-low-level-design.md) §2. The values are illustrative; they are not the hash of the text as written.

### Revision state timeline

```
REV-1  DRAFT ──submit──▶ IN_REVIEW ──changes requested──▶ CHANGES_REQUESTED
                                                              │
                                                              ▼
REV-1  SUPERSEDED ◀──edit creates REV-2───────────────────────┘

REV-2  DRAFT ──submit──▶ IN_REVIEW ──approve──▶ APPROVED
                                                  │
                                                  ▼
REV-2  SUPERSEDED ◀──edit creates REV-3───────────┘

REV-3  DRAFT ──submit──▶ IN_REVIEW ──edit creates REV-4──▶ SUPERSEDED

REV-4  DRAFT ──submit──▶ IN_REVIEW ──approve──▶ APPROVED
```

---

## Decisions

| ID | Revision | Reviewer | Outcome | Reason | Hash | Decided |
|---|---|---|---|---|---|---|
| `DEC-9001` | `REV-1042-1` | `USR-REV-1` | `CHANGES_REQUESTED` | “Audience is too broad and the offer is not stated. Narrow it to lapsed customers in Mumbai and Pune, and name the bundle price.” | `H1` | 10:31 |
| `DEC-9002` | `REV-1042-2` | `USR-REV-1` | `APPROVED` | — | `H2` | 11:02 |
| `DEC-9003` | `REV-1042-4` | `USR-REV-1` | `APPROVED` | — | `H4` | 11:32 |

There is **no** decision for `REV-1042-3`. The stale approval attempt at 11:27 was rejected before a row was written. That absence is part of the evidence.

---

## Schedules

| ID | Campaign | Revision | Decision | Start | State | Created | Cancelled | Reason |
|---|---|---|---|---|---|---|---|---|
| `SCH-7001` | `CMP-1042` | `REV-1042-2` | `DEC-9002` | 2026-11-08 10:00 IST | `CANCELLED` | 11:05 | 11:20 | `REVISION_SUPERSEDED` |
| `SCH-7002` | `CMP-1042` | `REV-1042-4` | `DEC-9003` | 2026-11-08 10:00 IST | `SCHEDULED` | 11:35 | — | — |

`SCH-7001` was cancelled in the same transaction that created `REV-1042-3`. `SCH-7002` is the only active schedule.

---

## Audit trail

The illustrative sequence. Each row is written in the same transaction as the state change it records.

| # | Time | Actor | Action | From | To | Metadata |
|---|---|---|---|---|---|---|
| 1 | 10:15 | `USR-MKT-1` | `REVISION_CREATED` | — | `DRAFT` | `revisionId: REV-1042-1` |
| 2 | 10:22 | `USR-MKT-1` | `REVISION_SUBMITTED` | `DRAFT` | `IN_REVIEW` | `revisionId: REV-1042-1` |
| 3 | 10:31 | `USR-REV-1` | `DECISION_CHANGES_REQUESTED` | `IN_REVIEW` | `CHANGES_REQUESTED` | `decisionId: DEC-9001` |
| 4 | 10:45 | `USR-MKT-1` | `REVISION_CREATED` | — | `DRAFT` | `revisionId: REV-1042-2`, `supersedesRevisionId: REV-1042-1` |
| 5 | 10:47 | `USR-MKT-1` | `REVISION_SUBMITTED` | `DRAFT` | `IN_REVIEW` | `revisionId: REV-1042-2` |
| 6 | 11:02 | `USR-REV-1` | `DECISION_APPROVED` | `IN_REVIEW` | `APPROVED` | `decisionId: DEC-9002` |
| 7 | 11:05 | `USR-MKT-1` | `SCHEDULE_CREATED` | — | `SCHEDULED` | `scheduleId: SCH-7001`, `decisionId: DEC-9002` |
| 8 | 11:20 | `USR-MKT-1` | `REVISION_CREATED` | — | `DRAFT` | `revisionId: REV-1042-3`, `supersedesRevisionId: REV-1042-2` |
| 9 | 11:20 | `USR-MKT-1` | `SCHEDULE_CANCELLED` | `SCHEDULED` | `CANCELLED` | `scheduleId: SCH-7001`, `reason: REVISION_SUPERSEDED` |
| 10 | 11:22 | `USR-MKT-1` | `REVISION_SUBMITTED` | `DRAFT` | `IN_REVIEW` | `revisionId: REV-1042-3` |
| 11 | 11:26 | `USR-MKT-1` | `REVISION_CREATED` | — | `DRAFT` | `revisionId: REV-1042-4`, `supersedesRevisionId: REV-1042-3` |
| 12 | 11:30 | `USR-MKT-1` | `REVISION_SUBMITTED` | `DRAFT` | `IN_REVIEW` | `revisionId: REV-1042-4` |
| 13 | 11:32 | `USR-REV-1` | `DECISION_APPROVED` | `IN_REVIEW` | `APPROVED` | `decisionId: DEC-9003` |
| 14 | 11:35 | `USR-MKT-1` | `SCHEDULE_CREATED` | — | `SCHEDULED` | `scheduleId: SCH-7002`, `decisionId: DEC-9003` |

**No row 15.** The stale approval attempt at 11:27 produced no audit event, because it produced no state change.

---

## Idempotency keys

| Label | UUID | Command | State |
|---|---|---|---|
| `KEY-CREATE` | `019a2f7c-8f1e-7c3a-9b2d-6a4e5f6d7c8b` | Create campaign | `COMPLETED` |
| `KEY-SUBMIT-1` | `019a2f7c-9a10-7d4b-8c3e-5f6a7b8c9d0e` | Submit revision 1 | `COMPLETED` |
| `KEY-DEC-1` | `019a2f7c-a1b2-7e5c-9d4f-6a7b8c9d0e1f` | Request changes on revision 1 | `COMPLETED` |
| `KEY-EDIT-2` | `019a2f7c-b2c3-7f6d-8e5a-7b8c9d0e1f2a` | Create revision 2 | `COMPLETED` |
| `KEY-SUBMIT-2` | `019a2f7c-c3d4-7a8e-9f6b-8c9d0e1f2a3b` | Submit revision 2 | `COMPLETED` |
| `KEY-DEC-2` | `019a2f7c-d4e5-7b9f-8a7c-9d0e1f2a3b4c` | Approve revision 2 | `COMPLETED` |
| `KEY-SCHED-1` | `019a2f7c-e5f6-7c0a-9b8d-0e1f2a3b4c5d` | Schedule revision 2 | `COMPLETED` |
| `KEY-EDIT-3` | `019a2f7c-f6a7-7d1b-8c9e-1f2a3b4c5d6e` | Create revision 3 | `COMPLETED` |
| `KEY-SUBMIT-3` | `019a2f7c-07b8-7e2c-9d0f-2a3b4c5d6e7f` | Submit revision 3 | `COMPLETED` |
| `KEY-EDIT-4` | `019a2f7c-18c9-7f3d-8e1a-3b4c5d6e7f80` | Create revision 4 | `COMPLETED` |
| `KEY-SUBMIT-4` | `019a2f7c-29da-704e-9f2b-4c5d6e7f8091` | Submit revision 4 | `COMPLETED` |
| `KEY-DEC-3` | `019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2` | Approve revision 4 | `COMPLETED` (response lost, then replayed) |
| `KEY-SCHED-2` | `019a2f7c-4bfc-726a-9b4d-6e7f8091a2b3` | Schedule revision 4 | `COMPLETED` |
| `KEY-DEC-STALE` | `019a2f7c-5c0d-737b-8c5e-7f8091a2b3c4` | Stale approval on revision 3 | **rolled back** (no row) |

The stale key is deliberately absent from the table. A failed command rolls back its key, so the client can try again against the new state.

---

## Fixture summary for a demo

```
Campaign:   CMP-1042 · Diwali Reset · current REV-1042-4
Marketer:   USR-MKT-1 · Meera
Reviewer:   USR-REV-1 · Arjun
Decisions:  DEC-9001 (changes, REV-1), DEC-9002 (approve, REV-2), DEC-9003 (approve, REV-4)
Schedules:  SCH-7001 (REV-2, cancelled), SCH-7002 (REV-4, scheduled)
Audit:      14 events
```

If a judge asks “show me the state”, this table is the answer. The UI is a projection of it.
