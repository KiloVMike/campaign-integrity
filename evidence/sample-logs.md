# Sample Logs

**Illustrative structured logs, traces, and metrics**

These lines are constructed from the canonical fixture in [`sample-data.md`](sample-data.md). They are **not captured from a running system**. Field names follow the log schema in [`06-verification-and-diagnostics.md`](../06-verification-and-diagnostics.md) §5.1.

The purpose is to show how one command can be followed from a tap to an audit row — and how the system distinguishes **committed**, **rejected**, and **replayed**.

---

## 1. What logs are for — and what they are not

Logs answer the operational question: *why did this request behave this way?*

The audit table answers the business question: *who changed what, and when?*

| | Audit events | Logs |
|---|---|---|
| Source of truth | **Yes** for domain history | No |
| Storage | PostgreSQL, append-only | Log sink, 30-day retention |
| Contents | Actor, action, states, decision ID, reason | IDs, timings, error codes |
| Missing row means | Integrity incident | Observability gap |

A missing log line is not proof that nothing happened. A missing audit row is an incident. The design keeps those two failure modes separate.

---

## 2. Correlation keys

| Key | Scope | Reused on retry? | Why |
|---|---|---|---|
| `requestId` | One **logical command** | **Yes** | The audit event and the retry must point at the same command |
| `traceId` | One **physical HTTP request** | No — a retry gets a new trace | The retry is a different network event |
| `idempotencyKey` | One **user intent** | **Yes**, across retries and restarts | A new key means a new intent |
| `campaignId` / `revisionId` | Domain scope | — | Narrows an investigation |
| `auditEventId` | One audit row | — | Matches the numbered trail in `sample-data.md` |
| `commandId` | One mobile outbox row | — | Local correlation on the device |

The split between `requestId` and `traceId` is deliberate. The replay of an approval 68 seconds later is a new trace, but it is the same logical command. Keeping `requestId` stable is what lets an investigator join the original commit to the replay.

---

## 3. Canonical request sequence

| # | Time (IST) | Request ID | Action | Actor | Result | Audit |
|---|---|---|---|---|---|---|
| 1 | 10:15:00 | `req_01JA7Z0001` | Create campaign → `REV-1` | Meera | `201` committed | 1 |
| 2 | 10:22:00 | `req_01JA7Z0002` | Submit `REV-1` | Meera | `200` committed | 2 |
| 3 | 10:31:00 | `req_01JA7Z0003` | Request changes on `REV-1` | Arjun | `200` committed | 3 |
| 4 | 10:45:00 | `req_01JA7Z0004` | Edit → `REV-2` | Meera | `200` committed | 4 |
| 5 | 10:47:00 | `req_01JA7Z0005` | Submit `REV-2` | Meera | `200` committed | 5 |
| 6 | 11:02:03 | `req_01JA7Z6K3M8Q2V5N4T9R1C0B7X` | Approve `REV-2` | Arjun | `200` committed | 6 |
| 7 | 11:05:00 | `req_01JA7Z0007` | Schedule `REV-2` (`SCH-7001`) | Meera | `201` committed | 7 |
| 8 | 11:20:00 | `req_01JA7Z0008` | Edit → `REV-3`; cancel `SCH-7001` | Meera | `200` committed | 8, 9 |
| 9 | 11:22:00 | `req_01JA7Z0009` | Submit `REV-3` | Meera | `200` committed | 10 |
| 10 | 11:26:00 | `req_01JA7Z000A` | Edit → `REV-4` | Meera | `200` committed | 11 |
| 11 | 11:27:14 | `req_01JA7Z8N4P2Q6R8S0T2V4W6X8Y` | Approve `REV-3` (stale) | Arjun | `409` rejected | — |
| 12 | 11:30:00 | `req_01JA7Z000B` | Submit `REV-4` | Meera | `200` committed | 12 |
| 13 | 11:32:02 | `req_01JA7Z9P5Q3R7S9T1V3W5X7Y9Z` | Approve `REV-4` | Arjun | `200` committed, response lost | 13 |
| 14 | 11:33:10 | `req_01JA7Z9P5Q3R7S9T1V3W5X7Y9Z` | Retry approve `REV-4` | Arjun | `200` replayed | — |
| 15 | 11:35:02 | `req_01JA7ZA1B2C3D4E5F6G7H8J9K0` | Schedule `REV-4` (`SCH-7002`) | Meera | `201` committed | 14 |

Fourteen audit events, fifteen HTTP requests. The difference is the replay: it returns the stored response before any domain work. The extra audit event at 11:20 is the edit that creates `REV-3` **and** cancels `SCH-7001` in one transaction.

---

## 4. The full log sequence

### 4.1 Create campaign — 10:15:00

```json
{"ts":"2026-11-01T10:15:00.396+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7Z0001","traceId":"3f9a1c7e5b2d8460a1c3e5f7092b4d68","actorId":"USR-MKT-1","actorRole":"MARKETER","campaignId":"CMP-1042","revisionId":"REV-1042-1","action":"REVISION_CREATED","fromState":null,"toState":"DRAFT","outcome":"committed","auditEventId":1}
{"ts":"2026-11-01T10:15:00.412+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z0001","traceId":"3f9a1c7e5b2d8460a1c3e5f7092b4d68","actorId":"USR-MKT-1","actorRole":"MARKETER","route":"POST /v1/campaigns","campaignId":"CMP-1042","revisionId":"REV-1042-1","action":"REVISION_CREATED","outcome":"committed","status":201,"durationMs":42,"idempotencyKey":"019a2f7c-8f1e-7c3a-9b2d-6a4e5f6d7c8b","idempotentReplay":false}
```

### 4.2 Submit revision 1 — 10:22:00

```json
{"ts":"2026-11-01T10:22:00.488+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7Z0002","traceId":"a71c3e59d2f8460b1e3a5c7f9024d6b8","actorId":"USR-MKT-1","actorRole":"MARKETER","campaignId":"CMP-1042","revisionId":"REV-1042-1","action":"REVISION_SUBMITTED","fromState":"DRAFT","toState":"IN_REVIEW","outcome":"committed","auditEventId":2}
{"ts":"2026-11-01T10:22:00.501+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z0002","traceId":"a71c3e59d2f8460b1e3a5c7f9024d6b8","actorId":"USR-MKT-1","actorRole":"MARKETER","route":"POST /v1/campaigns/:id/submit","campaignId":"CMP-1042","revisionId":"REV-1042-1","action":"REVISION_SUBMITTED","outcome":"committed","status":200,"durationMs":27,"idempotencyKey":"019a2f7c-9a10-7d4b-8c3e-5f6a7b8c9d0e","idempotentReplay":false}
```

### 4.3 Request changes — 10:31:00

```json
{"ts":"2026-11-01T10:31:00.933+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7Z0003","traceId":"c41e7a9b3d5f8246a0c2e4f6081b3d57","actorId":"USR-REV-1","actorRole":"REVIEWER","campaignId":"CMP-1042","revisionId":"REV-1042-1","action":"DECISION_CHANGES_REQUESTED","fromState":"IN_REVIEW","toState":"CHANGES_REQUESTED","outcome":"committed","auditEventId":3,"decisionId":"DEC-9001"}
{"ts":"2026-11-01T10:31:00.950+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z0003","traceId":"c41e7a9b3d5f8246a0c2e4f6081b3d57","actorId":"USR-REV-1","actorRole":"REVIEWER","route":"POST /v1/campaigns/:id/decisions","campaignId":"CMP-1042","revisionId":"REV-1042-1","action":"DECISION_CHANGES_REQUESTED","outcome":"committed","status":200,"durationMs":45,"idempotencyKey":"019a2f7c-a1b2-7e5c-9d4f-6a7b8c9d0e1f","idempotentReplay":false}
```

The log line carries `decisionId`, **not** the reviewer's reason. The free-text reason lives in `approval_decisions.reason` and `audit_events.metadata`, which have stricter access control. See §8.

### 4.4 Edit to revision 2 — 10:45:00

```json
{"ts":"2026-11-01T10:45:00.712+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7Z0004","traceId":"e83b5d1f7a2c9460b3d5f7091e4a6c82","actorId":"USR-MKT-1","actorRole":"MARKETER","campaignId":"CMP-1042","revisionId":"REV-1042-2","action":"REVISION_CREATED","fromState":null,"toState":"DRAFT","outcome":"committed","auditEventId":4,"supersedesRevisionId":"REV-1042-1"}
{"ts":"2026-11-01T10:45:00.735+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z0004","traceId":"e83b5d1f7a2c9460b3d5f7091e4a6c82","actorId":"USR-MKT-1","actorRole":"MARKETER","route":"PATCH /v1/campaigns/:id","campaignId":"CMP-1042","revisionId":"REV-1042-2","action":"REVISION_CREATED","outcome":"committed","status":200,"durationMs":51,"idempotencyKey":"019a2f7c-b2c3-7f6d-8e5a-7b8c9d0e1f2a","idempotentReplay":false}
```

No `SCHEDULE_CANCELLED` event: `REV-1` was never scheduled.

### 4.5 Submit revision 2 — 10:47:00

```json
{"ts":"2026-11-01T10:47:00.469+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7Z0005","traceId":"1d6f9b3e5a7c2048d1f3b5e7092a4c68","actorId":"USR-MKT-1","actorRole":"MARKETER","campaignId":"CMP-1042","revisionId":"REV-1042-2","action":"REVISION_SUBMITTED","fromState":"DRAFT","toState":"IN_REVIEW","outcome":"committed","auditEventId":5}
{"ts":"2026-11-01T10:47:00.482+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z0005","traceId":"1d6f9b3e5a7c2048d1f3b5e7092a4c68","actorId":"USR-MKT-1","actorRole":"MARKETER","route":"POST /v1/campaigns/:id/submit","campaignId":"CMP-1042","revisionId":"REV-1042-2","action":"REVISION_SUBMITTED","outcome":"committed","status":200,"durationMs":29,"idempotencyKey":"019a2f7c-c3d4-7a8e-9f6b-8c9d0e1f2a3b","idempotentReplay":false}
```

### 4.6 Approve revision 2 — 11:02:03

```json
{"ts":"2026-11-01T11:02:02.980+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7Z6K3M8Q2V5N4T9R1C0B7X","traceId":"5a2c8e4f6b1d3709c2e4a6f8013b5d79","actorId":"USR-REV-1","actorRole":"REVIEWER","campaignId":"CMP-1042","revisionId":"REV-1042-2","action":"DECISION_APPROVED","fromState":"IN_REVIEW","toState":"APPROVED","outcome":"committed","auditEventId":6,"decisionId":"DEC-9002"}
{"ts":"2026-11-01T11:02:03.001+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z6K3M8Q2V5N4T9R1C0B7X","traceId":"5a2c8e4f6b1d3709c2e4a6f8013b5d79","actorId":"USR-REV-1","actorRole":"REVIEWER","route":"POST /v1/campaigns/:id/decisions","campaignId":"CMP-1042","revisionId":"REV-1042-2","action":"DECISION_APPROVED","outcome":"committed","status":200,"durationMs":33,"idempotencyKey":"019a2f7c-d4e5-7b9f-8a7c-9d0e1f2a3b4c","idempotentReplay":false}
```

### 4.7 Schedule revision 2 — 11:05:00

```json
{"ts":"2026-11-01T11:05:00.641+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7Z0007","traceId":"b9d3f7a1c5e82460d3f5b7091a4c6e82","actorId":"USR-MKT-1","actorRole":"MARKETER","campaignId":"CMP-1042","revisionId":"REV-1042-2","action":"SCHEDULE_CREATED","fromState":null,"toState":"SCHEDULED","outcome":"committed","auditEventId":7,"scheduleId":"SCH-7001","decisionId":"DEC-9002"}
{"ts":"2026-11-01T11:05:00.662+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z0007","traceId":"b9d3f7a1c5e82460d3f5b7091a4c6e82","actorId":"USR-MKT-1","actorRole":"MARKETER","route":"POST /v1/campaigns/:id/schedule","campaignId":"CMP-1042","revisionId":"REV-1042-2","action":"SCHEDULE_CREATED","outcome":"committed","status":201,"durationMs":61,"idempotencyKey":"019a2f7c-e5f6-7c0a-9b8d-0e1f2a3b4c5d","idempotentReplay":false}
```

### 4.8 Edit to revision 3 — approval invalidated, schedule cancelled — 11:20:00

One request, **two** domain events, one transaction:

```json
{"ts":"2026-11-01T11:20:00.690+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7Z0008","traceId":"7c1e5a9d3f6b2804e1c3a5f7092b4d68","actorId":"USR-MKT-1","actorRole":"MARKETER","campaignId":"CMP-1042","revisionId":"REV-1042-3","action":"REVISION_CREATED","fromState":null,"toState":"DRAFT","outcome":"committed","auditEventId":8,"supersedesRevisionId":"REV-1042-2"}
{"ts":"2026-11-01T11:20:00.701+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7Z0008","traceId":"7c1e5a9d3f6b2804e1c3a5f7092b4d68","actorId":"USR-MKT-1","actorRole":"MARKETER","campaignId":"CMP-1042","revisionId":"REV-1042-2","action":"SCHEDULE_CANCELLED","fromState":"SCHEDULED","toState":"CANCELLED","outcome":"committed","auditEventId":9,"scheduleId":"SCH-7001","reason":"REVISION_SUPERSEDED"}
{"ts":"2026-11-01T11:20:00.720+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z0008","traceId":"7c1e5a9d3f6b2804e1c3a5f7092b4d68","actorId":"USR-MKT-1","actorRole":"MARKETER","route":"PATCH /v1/campaigns/:id","campaignId":"CMP-1042","revisionId":"REV-1042-3","action":"REVISION_CREATED","outcome":"committed","status":200,"durationMs":57,"idempotencyKey":"019a2f7c-f6a7-7d1b-8c9e-1f2a3b4c5d6e","idempotentReplay":false,"cancelledScheduleId":"SCH-7001"}
```

The two audit rows share the same `requestId` and `traceId`. If an investigator finds either one, they find the other. There is no committed moment where `SCH-7001` is still `SCHEDULED` and `REV-3` is current.

### 4.9 Submit revision 3 — 11:22:00

```json
{"ts":"2026-11-01T11:22:00.474+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7Z0009","traceId":"d4f8b2e6a1c93570f2d4b6e8013a5c79","actorId":"USR-MKT-1","actorRole":"MARKETER","campaignId":"CMP-1042","revisionId":"REV-1042-3","action":"REVISION_SUBMITTED","fromState":"DRAFT","toState":"IN_REVIEW","outcome":"committed","auditEventId":10}
{"ts":"2026-11-01T11:22:00.487+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z0009","traceId":"d4f8b2e6a1c93570f2d4b6e8013a5c79","actorId":"USR-MKT-1","actorRole":"MARKETER","route":"POST /v1/campaigns/:id/submit","campaignId":"CMP-1042","revisionId":"REV-1042-3","action":"REVISION_SUBMITTED","outcome":"committed","status":200,"durationMs":26,"idempotencyKey":"019a2f7c-07b8-7e2c-9d0f-2a3b4c5d6e7f","idempotentReplay":false}
```

### 4.10 Edit to revision 4 — 11:26:00

```json
{"ts":"2026-11-01T11:26:00.655+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7Z000A","traceId":"2e6a8c1f4b7d3905a2c4e6f8013b5d97","actorId":"USR-MKT-1","actorRole":"MARKETER","campaignId":"CMP-1042","revisionId":"REV-1042-4","action":"REVISION_CREATED","fromState":null,"toState":"DRAFT","outcome":"committed","auditEventId":11,"supersedesRevisionId":"REV-1042-3"}
{"ts":"2026-11-01T11:26:00.679+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z000A","traceId":"2e6a8c1f4b7d3905a2c4e6f8013b5d97","actorId":"USR-MKT-1","actorRole":"MARKETER","route":"PATCH /v1/campaigns/:id","campaignId":"CMP-1042","revisionId":"REV-1042-4","action":"REVISION_CREATED","outcome":"committed","status":200,"durationMs":49,"idempotencyKey":"019a2f7c-18c9-7f3d-8e1a-3b4c5d6e7f80","idempotentReplay":false}
```

No `SCHEDULE_CANCELLED` event: `SCH-7001` was already cancelled at 11:20.

### 4.11 Stale approval rejected — 11:27:14

```json
{"ts":"2026-11-01T11:27:14.102+05:30","level":"warn","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z8N4P2Q6R8S0T2V4W6X8Y","traceId":"9f2c1a3b4c5d6e7f8a9b0c1d2e3f4a5b","actorId":"USR-REV-1","actorRole":"REVIEWER","route":"POST /v1/campaigns/:id/decisions","campaignId":"CMP-1042","revisionId":"REV-1042-3","action":"DECISION_APPROVED","outcome":"rejected","code":"REVISION_STALE","status":409,"durationMs":21,"idempotencyKey":"019a2f7c-5c0d-737b-8c5e-7f8091a2b3c4","currentRevisionId":"REV-1042-4"}
```

**There is no `domain.event` line.** That absence is the evidence: the transaction rolled back, including the idempotency key. No decision, no revision update, no audit row. A failed command leaves no trace that could be mistaken for a decision.

### 4.12 Submit revision 4 — 11:30:00

```json
{"ts":"2026-11-01T11:30:00.478+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7Z000B","traceId":"6b3d9f1a5c7e2408f3b5d7091a2c4e86","actorId":"USR-MKT-1","actorRole":"MARKETER","campaignId":"CMP-1042","revisionId":"REV-1042-4","action":"REVISION_SUBMITTED","fromState":"DRAFT","toState":"IN_REVIEW","outcome":"committed","auditEventId":12}
{"ts":"2026-11-01T11:30:00.491+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z000B","traceId":"6b3d9f1a5c7e2408f3b5d7091a2c4e86","actorId":"USR-MKT-1","actorRole":"MARKETER","route":"POST /v1/campaigns/:id/submit","campaignId":"CMP-1042","revisionId":"REV-1042-4","action":"REVISION_SUBMITTED","outcome":"committed","status":200,"durationMs":28,"idempotencyKey":"019a2f7c-29da-704e-9f2b-4c5d6e7f8091","idempotentReplay":false}
```

### 4.13 Approve revision 4 — committed, response lost — 11:32:02

```json
{"ts":"2026-11-01T11:32:02.401+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7Z9P5Q3R7S9T1V3W5X7Y9Z","traceId":"4bf92f3577b34da6a3ce929d0e0e4736","actorId":"USR-REV-1","actorRole":"REVIEWER","campaignId":"CMP-1042","revisionId":"REV-1042-4","action":"DECISION_APPROVED","fromState":"IN_REVIEW","toState":"APPROVED","outcome":"committed","auditEventId":13,"decisionId":"DEC-9003"}
{"ts":"2026-11-01T11:32:02.418+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z9P5Q3R7S9T1V3W5X7Y9Z","traceId":"4bf92f3577b34da6a3ce929d0e0e4736","actorId":"USR-REV-1","actorRole":"REVIEWER","route":"POST /v1/campaigns/:id/decisions","campaignId":"CMP-1042","revisionId":"REV-1042-4","action":"DECISION_APPROVED","outcome":"committed","status":200,"durationMs":38,"idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","idempotentReplay":false}
```

The server wrote the response. The phone never received it. The next client log line is a timeout, not a failure.

### 4.14 Retry with the same key — replayed — 11:33:10

```json
{"ts":"2026-11-01T11:33:10.664+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z9P5Q3R7S9T1V3W5X7Y9Z","traceId":"a4c8e2f6b1d93570c2e4a6f8013b5d79","actorId":"USR-REV-1","actorRole":"REVIEWER","route":"POST /v1/campaigns/:id/decisions","campaignId":"CMP-1042","revisionId":"REV-1042-4","action":"DECISION_APPROVED","outcome":"replayed","status":200,"durationMs":4,"idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","idempotentReplay":true}
```

**There is no second `domain.event` line.** The replay path returns the stored response before any domain work. The `requestId` is the original; the `traceId` is new because this is a new HTTP request. That is how the original commit and the retry stay joined without pretending the retry was the same network event.

### 4.15 Schedule revision 4 — 11:35:02

```json
{"ts":"2026-11-01T11:35:02.451+05:30","level":"info","service":"campaign-api","env":"prod","event":"domain.event","requestId":"req_01JA7ZA1B2C3D4E5F6G7H8J9K0","traceId":"8e2a6c4f1b9d3750a4c6e8f2013b5d79","actorId":"USR-MKT-1","actorRole":"MARKETER","campaignId":"CMP-1042","revisionId":"REV-1042-4","action":"SCHEDULE_CREATED","fromState":null,"toState":"SCHEDULED","outcome":"committed","auditEventId":14,"scheduleId":"SCH-7002","decisionId":"DEC-9003"}
{"ts":"2026-11-01T11:35:02.475+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7ZA1B2C3D4E5F6G7H8J9K0","traceId":"8e2a6c4f1b9d3750a4c6e8f2013b5d79","actorId":"USR-MKT-1","actorRole":"MARKETER","route":"POST /v1/campaigns/:id/schedule","campaignId":"CMP-1042","revisionId":"REV-1042-4","action":"SCHEDULE_CREATED","outcome":"committed","status":201,"durationMs":64,"idempotencyKey":"019a2f7c-4bfc-726a-9b4d-6e7f8091a2b3","idempotentReplay":false}
```

---

## 5. Mobile outbox logs

These are the client-side lines for the same lost response. The server was healthy; the phone was not sure.

```json
{"ts":"2026-11-01T11:32:00.812+05:30","level":"info","service":"campaign-mobile","env":"prod","deviceId":"dev_7f3a","event":"outbox.enqueued","commandId":"019a2f7c-3a00-7b1e-8c2d-6a4e5f6d7c8b","idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","type":"DECIDE","campaignId":"CMP-1042","revisionId":"REV-1042-4","state":"PENDING","attempt":0}
{"ts":"2026-11-01T11:32:00.840+05:30","level":"info","service":"campaign-mobile","env":"prod","deviceId":"dev_7f3a","event":"outbox.send_started","commandId":"019a2f7c-3a00-7b1e-8c2d-6a4e5f6d7c8b","idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","type":"DECIDE","state":"IN_FLIGHT","attempt":1}
{"ts":"2026-11-01T11:32:03.512+05:30","level":"warn","service":"campaign-mobile","env":"prod","deviceId":"dev_7f3a","event":"outbox.send_timed_out","commandId":"019a2f7c-3a00-7b1e-8c2d-6a4e5f6d7c8b","idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","type":"DECIDE","state":"PENDING","attempt":1,"code":"NETWORK_TIMEOUT","nextAttemptAt":"2026-11-01T11:32:08.512+05:30"}
{"ts":"2026-11-01T11:32:05.220+05:30","level":"info","service":"campaign-mobile","env":"prod","deviceId":"dev_7f3a","event":"outbox.deferred","commandId":"019a2f7c-3a00-7b1e-8c2d-6a4e5f6d7c8b","idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","type":"DECIDE","state":"PENDING","attempt":1,"reasonCode":"APP_BACKGROUNDED"}
{"ts":"2026-11-01T11:33:09.900+05:30","level":"info","service":"campaign-mobile","env":"prod","deviceId":"dev_7f3a","event":"outbox.resumed","commandId":"019a2f7c-3a00-7b1e-8c2d-6a4e5f6d7c8b","idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","type":"DECIDE","state":"PENDING","attempt":1,"pending":1}
{"ts":"2026-11-01T11:33:09.950+05:30","level":"info","service":"campaign-mobile","env":"prod","deviceId":"dev_7f3a","event":"outbox.send_started","commandId":"019a2f7c-3a00-7b1e-8c2d-6a4e5f6d7c8b","idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","type":"DECIDE","state":"IN_FLIGHT","attempt":2}
{"ts":"2026-11-01T11:33:10.664+05:30","level":"info","service":"campaign-mobile","env":"prod","deviceId":"dev_7f3a","event":"outbox.send_succeeded","commandId":"019a2f7c-3a00-7b1e-8c2d-6a4e5f6d7c8b","idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","type":"DECIDE","state":"DONE","attempt":2,"status":200,"idempotentReplay":true,"durationMs":714}
{"ts":"2026-11-01T11:33:10.702+05:30","level":"info","service":"campaign-mobile","env":"prod","deviceId":"dev_7f3a","event":"outbox.marked_done","commandId":"019a2f7c-3a00-7b1e-8c2d-6a4e5f6d7c8b","idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","type":"DECIDE","state":"DONE","attempt":2}
```

The client `durationMs` is 714 ms because it includes the network; the server line says 4 ms because it is processing time only. The two numbers measure different things. That is not a contradiction; it is a reminder to compare like with like.

### 5.1 Variant — the process dies before the timeout handler runs

If the app is killed after the send but before it can mark the row `PENDING`, the row stays `IN_FLIGHT`. On restart the sync engine reconciles instead of resending:

```json
{"ts":"2026-11-01T11:33:09.880+05:30","level":"info","service":"campaign-mobile","env":"prod","deviceId":"dev_7f3a","event":"outbox.restored","commandId":"019a2f7c-3a00-7b1e-8c2d-6a4e5f6d7c8b","idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","type":"DECIDE","state":"IN_FLIGHT","attempt":1,"pending":1}
{"ts":"2026-11-01T11:33:09.930+05:30","level":"info","service":"campaign-mobile","env":"prod","deviceId":"dev_7f3a","event":"outbox.reconcile_started","commandId":"019a2f7c-3a00-7b1e-8c2d-6a4e5f6d7c8b","idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","type":"DECIDE","state":"IN_FLIGHT","attempt":1}
{"ts":"2026-11-01T11:33:10.120+05:30","level":"info","service":"campaign-mobile","env":"prod","deviceId":"dev_7f3a","event":"outbox.reconcile_completed","commandId":"019a2f7c-3a00-7b1e-8c2d-6a4e5f6d7c8b","idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","type":"DECIDE","state":"DONE","attempt":1,"status":200,"commandState":"COMPLETED"}
{"ts":"2026-11-01T11:33:10.150+05:30","level":"info","service":"campaign-mobile","env":"prod","deviceId":"dev_7f3a","event":"outbox.marked_done","commandId":"019a2f7c-3a00-7b1e-8c2d-6a4e5f6d7c8b","idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","type":"DECIDE","state":"DONE","attempt":1}
```

No resend, no replay, no duplicate. This is test **T-21**.

---

## 6. Metrics snapshot

Snapshot at `2026-11-01T11:40:00+05:30`, after the full journey. Illustrative values.

```text
# HELP campaign_command_total Commands received, by type and outcome.
# TYPE campaign_command_total counter
campaign_command_total{type="create",outcome="committed"} 1
campaign_command_total{type="edit",outcome="committed"} 3
campaign_command_total{type="submit",outcome="committed"} 4
campaign_command_total{type="decide",outcome="committed"} 3
campaign_command_total{type="decide",outcome="rejected"} 1
campaign_command_total{type="decide",outcome="replayed"} 1
campaign_command_total{type="schedule",outcome="committed"} 2
campaign_command_total{type="schedule",outcome="rejected"} 0

# HELP schedule_rejected_total Schedule commands rejected, by error code.
# TYPE schedule_rejected_total counter
schedule_rejected_total{code="REVISION_STALE"} 0
schedule_rejected_total{code="APPROVAL_INVALID"} 0
schedule_rejected_total{code="ALREADY_SCHEDULED"} 0
schedule_rejected_total{code="CONTENT_HASH_MISMATCH"} 0

# HELP approval_conflict_total Approval commands rejected, by reason.
# TYPE approval_conflict_total counter
approval_conflict_total{reason="REVISION_STALE"} 1

# HELP idempotency_replay_total Replays served from the key store.
# TYPE idempotency_replay_total counter
idempotency_replay_total{endpoint="POST /v1/campaigns/:id/decisions"} 1

# HELP outbox_pending_age_seconds Age of the oldest pending mobile command.
# TYPE outbox_pending_age_seconds gauge
outbox_pending_age_seconds{command_type="DECIDE"} 0

# HELP outbox_failed_total Commands that exhausted retries.
# TYPE outbox_failed_total counter
outbox_failed_total{command_type="DECIDE"} 0

# HELP db_transaction_retry_total Transactions retried after a transient error.
# TYPE db_transaction_retry_total counter
db_transaction_retry_total{reason="serialization_failure"} 0
db_transaction_retry_total{reason="deadlock"} 0

# HELP audit_write_failures_total Audit inserts that failed. Must stay zero.
# TYPE audit_write_failures_total counter
audit_write_failures_total 0

# HELP integrity_violation_total Invariant checks that found a violation. Must stay zero.
# TYPE integrity_violation_total counter
integrity_violation_total{kind="active_schedule_without_approval"} 0
integrity_violation_total{kind="multiple_active_schedules"} 0
integrity_violation_total{kind="duplicate_decision"} 0

# HELP campaign_command_duration_ms Server processing time, by command type.
# TYPE campaign_command_duration_ms histogram
campaign_command_duration_ms_bucket{type="decide",le="10"} 1
campaign_command_duration_ms_bucket{type="decide",le="25"} 2
campaign_command_duration_ms_bucket{type="decide",le="50"} 5
campaign_command_duration_ms_bucket{type="decide",le="100"} 5
campaign_command_duration_ms_bucket{type="decide",le="+Inf"} 5
campaign_command_duration_ms_sum{type="decide"} 141
campaign_command_duration_ms_count{type="decide"} 5

campaign_command_duration_ms_bucket{type="schedule",le="50"} 0
campaign_command_duration_ms_bucket{type="schedule",le="100"} 2
campaign_command_duration_ms_bucket{type="schedule",le="+Inf"} 2
campaign_command_duration_ms_sum{type="schedule"} 125
campaign_command_duration_ms_count{type="schedule"} 2
```

The decision histogram has five observations: 45 ms (changes requested), 33 ms (approve `REV-2`), 21 ms (stale rejection), 38 ms (approve `REV-4`), and 4 ms (replay). Sum 141 ms.

### 6.1 Outbox age during the incident

A single snapshot at 11:40 shows zero because the command completed. The range query tells the story:

| Time | `outbox_pending_age_seconds{command_type="DECIDE"}` | What happened |
|---|---|---|
| 11:32:15 | 14 | Timed out, waiting for backoff |
| 11:33:05 | 64 | App backgrounded; row still pending |
| 11:33:12 | 0 | Replay applied; row `DONE` |

The 300-second alert threshold was never approached. That is why the incident is a warning in the logs, not a page.

### 6.2 Alerts at the snapshot

| Alert | Expression | State | Evidence |
|---|---|---|---|
| Audit write failure | `audit_write_failures_total > 0` | inactive | 0 |
| Integrity violation | `integrity_violation_total > 0` | inactive | 0 |
| Hash mismatch | `schedule_rejected_total{code="CONTENT_HASH_MISMATCH"} > 0` | inactive | 0 |
| Stuck outbox | `outbox_pending_age_seconds > 300` | inactive | peak 64 s |
| Replay storm | replay ratio > 0.2 | inactive | 1 / 15 = 6.7% |
| Slow commands | p95 > 1000 ms | inactive | max 64 ms |

A stale **decision** increments `approval_conflict_total{reason="REVISION_STALE"}`. A stale **schedule** would increment `schedule_rejected_total{code="REVISION_STALE"}`. This fixture contains the former, not the latter; that is why the schedule counter is zero despite the 409.

---

## 7. Traces

### 7.1 Approval that committed before the client timed out

```text
Trace 4bf92f3577b34da6a3ce929d0e0e4736
requestId req_01JA7Z9P5Q3R7S9T1V3W5X7Y9Z

11:32:02.380  POST /v1/campaigns/CMP-1042/decisions
  ├─ auth.verify                 2 ms
  ├─ idempotency.claim           3 ms
  ├─ campaign.lock               5 ms
  ├─ decision.validate           4 ms
  ├─ decision.insert             6 ms
  ├─ revision.update             3 ms
  ├─ audit.append                4 ms
  ├─ idempotency.complete        2 ms
  └─ commit                      9 ms
11:32:02.418  response written (38 ms)

11:32:03.512  client timeout — response never received
```

The trace ends in success. The client log ends in a timeout. Both are true. The idempotency key is what turns that ambiguity into exactly one effect.

### 7.2 Schedule transaction

```text
Trace 8e2a6c4f1b9d3750a4c6e8f2013b5d79
requestId req_01JA7ZA1B2C3D4E5F6G7H8J9K0

11:35:02.411  POST /v1/campaigns/CMP-1042/schedule
  ├─ request.parse               4 ms
  ├─ auth.verify                 2 ms
  ├─ idempotency.claim           4 ms
  ├─ db.pool.wait               16 ms
  ├─ campaign.lock               6 ms
  ├─ eligibility.evaluate        2 ms
  ├─ schedule.insert             7 ms
  ├─ audit.append                5 ms
  ├─ idempotency.complete        3 ms
  ├─ response.serialize          3 ms
  └─ commit                     12 ms
11:35:02.475  response written (64 ms)
```

The `audit.append` span is inside the same transaction as `schedule.insert`. If it fails, the commit does not happen. That is the property the trace is meant to make visible.

---

## 8. Log queries for an investigation

```text
# One logical command, including the replay
requestId = "req_01JA7Z9P5Q3R7S9T1V3W5X7Y9Z"
# → 3 lines: domain.event 11:32:02.401, request completed 11:32:02.418,
#            request replayed 11:33:10.664

# Every attempt for one intent, across devices
idempotencyKey = "019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2"
# → the same 3 lines

# Every rejection for a campaign
campaignId = "CMP-1042" AND outcome = "rejected"
# → 1 line: REVISION_STALE at 11:27:14

# Every domain event, in order
campaignId = "CMP-1042" AND event = "domain.event"
# → 14 lines, auditEventId 1 through 14

# Every replay in the window
outcome = "replayed"
# → 1 line
```

The first query is the one to run when a user says “I approved, but the app still says pending.” If the `domain.event` line exists and the `http.request.completed` line says `committed`, the server did its job. The remaining question is on the device.

---

## 9. What is deliberately absent

| Data | In logs? | Where it lives instead |
|---|---|---|
| Campaign objective | **No** | `campaign_revisions.objective` |
| Audience definition | **No** | `campaign_revisions.audience` |
| Budget | **No** | `campaign_revisions.budget_minor` |
| Reviewer's free-text reason | **No** | `approval_decisions.reason`, `audit_events.metadata` |
| User name or email | **No** | `users` |
| Access token | **No** | Never logged |
| Full request body | **No** | Only `idempotency_keys.request_hash` |
| Actor ID, role | Yes | Needed for diagnosis |
| Campaign/revision IDs | Yes | Domain scope |
| Action, state, error code | Yes | Behaviour |
| Duration, status | Yes | Performance and outcome |

A support engineer can see that `DEC-9001` happened, who made it, and when. They cannot read the reason from the logs. That is intentional: diagnosis needs identifiers, not content.

The audit table is not a log sink. It is a domain record with stricter access control, and it is written in the same transaction as the change it describes.

---

## 10. What these logs cannot prove

- **They are not a test report.** No line was captured from a running system. The test matrix in [`06-verification-and-diagnostics.md`](../06-verification-and-diagnostics.md) is specified, not executed.
- **They are not the source of truth.** The audit table and the current row state are. A log line can be lost, sampled, or expired; an audit row cannot be updated or deleted by the application role.
- **A missing line is not proof of no change.** Log retention is 30 days. The audit trail is the durable record.
- **A replay line proves the server returned a stored response.** It does not prove the client applied it. The next client `outbox.marked_done` line is the evidence for that.
- **Timestamps are server-authoritative in the API, but log ingestion can reorder lines.** Sort by `ts`, then by `auditEventId` for domain events.
- **Metrics are aggregates.** They show pressure and trends; they cannot explain a single request. Use the `requestId` for that.

If a judge asks “show me the evidence”, show the audit trail first. These logs are the diagnostic layer that explains how the system behaved while producing it.
