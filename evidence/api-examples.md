# API Examples

**Illustrative request and response payloads**

These examples match the identifiers in [`sample-data.md`](sample-data.md) and the contracts in [`03-low-level-design.md`](../03-low-level-design.md) §7. They are not captured from a running server.

Conventions:

- All paths are under `/v1`.
- All mutating requests carry `Idempotency-Key`.
- Times are ISO-8601 with the IST offset.
- Money is integer paise.
- Errors use the `{ "error": { ... }, "meta": { ... } }` envelope.

---

## 1. Create campaign

```http
POST /v1/campaigns
Idempotency-Key: 019a2f7c-8f1e-7c3a-9b2d-6a4e5f6d7c8b
Content-Type: application/json

{
  "name": "Diwali Reset",
  "objective": "Win back lapsed customers with a festive bundle",
  "audience": "All customers in India, 18–55",
  "channel": "INSTAGRAM",
  "budgetMinor": 50000000,
  "currency": "INR"
}
```

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "data": {
    "campaign": {
      "id": "CMP-1042",
      "name": "Diwali Reset",
      "createdBy": "USR-MKT-1",
      "currentRevisionId": "REV-1042-1",
      "createdAt": "2026-11-01T10:15:00+05:30"
    },
    "currentRevision": {
      "id": "REV-1042-1",
      "revisionNumber": 1,
      "state": "DRAFT",
      "objective": "Win back lapsed customers with a festive bundle",
      "audience": "All customers in India, 18–55",
      "channel": "INSTAGRAM",
      "budgetMinor": 50000000,
      "currency": "INR",
      "contentHash": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b"
    },
    "allowedActions": ["EDIT", "SUBMIT"]
  },
  "meta": {
    "requestId": "req_01JA7Z0001",
    "serverTime": "2026-11-01T10:15:00+05:30"
  }
}
```

---

## 2. Submit for review

```http
POST /v1/campaigns/CMP-1042/submit
Idempotency-Key: 019a2f7c-9a10-7d4b-8c3e-5f6a7b8c9d0e
Content-Type: application/json

{
  "revisionId": "REV-1042-1",
  "expectedContentHash": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b"
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "revision": {
      "id": "REV-1042-1",
      "state": "IN_REVIEW",
      "submittedAt": "2026-11-01T10:22:00+05:30"
    },
    "allowedActions": ["VIEW_HISTORY"]
  },
  "meta": {
    "requestId": "req_01JA7Z0002",
    "serverTime": "2026-11-01T10:22:00+05:30"
  }
}
```

---

## 3. Request changes

```http
POST /v1/campaigns/CMP-1042/decisions
Idempotency-Key: 019a2f7c-a1b2-7e5c-9d4f-6a7b8c9d0e1f
Content-Type: application/json

{
  "revisionId": "REV-1042-1",
  "outcome": "CHANGES_REQUESTED",
  "reason": "Audience is too broad and the offer is not stated. Narrow it to lapsed customers in Mumbai and Pune, and name the bundle price.",
  "expectedContentHash": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b"
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "decision": {
      "id": "DEC-9001",
      "revisionId": "REV-1042-1",
      "reviewerId": "USR-REV-1",
      "outcome": "CHANGES_REQUESTED",
      "reason": "Audience is too broad and the offer is not stated. Narrow it to lapsed customers in Mumbai and Pune, and name the bundle price.",
      "decidedAt": "2026-11-01T10:31:00+05:30"
    },
    "campaign": {
      "id": "CMP-1042",
      "approvalStatus": "CHANGES_REQUESTED",
      "allowedActions": ["EDIT", "VIEW_HISTORY"]
    }
  },
  "meta": {
    "requestId": "req_01JA7Z0003",
    "serverTime": "2026-11-01T10:31:00+05:30"
  }
}
```

---

## 4. Edit an approved campaign (copy-on-write)

```http
PATCH /v1/campaigns/CMP-1042
Idempotency-Key: 019a2f7c-f6a7-7d1b-8c9e-1f2a3b4c5d6e
Content-Type: application/json

{
  "expectedContentHash": "4b1d0c7a9e2f8a6c3d5e1f0b7c9a2d4e6f8b1c3d5e7a9f0b2c4d6e8f1a3b5c7d",
  "budgetMinor": 80000000
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "revision": {
      "id": "REV-1042-3",
      "revisionNumber": 3,
      "state": "DRAFT",
      "budgetMinor": 80000000,
      "contentHash": "7f6e5d4c3b2a1908f7e6d5c4b3a29180f6e5d4c3b2a1908f7e6d5c4b3a291807"
    },
    "revisionCreated": true,
    "approvalInvalidated": true,
    "cancelledScheduleId": "SCH-7001"
  },
  "meta": {
    "requestId": "req_01JA7Z0008",
    "serverTime": "2026-11-01T11:20:00+05:30"
  }
}
```

**What the client should show**

> **Revision 3 created**  
> The approval for Revision 2 is no longer valid.  
> The schedule for 8 Nov, 10:00 has been cancelled.  
> Submit Revision 3 for review to schedule it again.

---

## 5. Approve the current revision

```http
POST /v1/campaigns/CMP-1042/decisions
Idempotency-Key: 019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2
Content-Type: application/json

{
  "revisionId": "REV-1042-4",
  "outcome": "APPROVED",
  "reason": null,
  "expectedContentHash": "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4"
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "decision": {
      "id": "DEC-9003",
      "revisionId": "REV-1042-4",
      "reviewerId": "USR-REV-1",
      "outcome": "APPROVED",
      "reason": null,
      "revisionContentHash": "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4",
      "decidedAt": "2026-11-01T11:32:02+05:30"
    },
    "campaign": {
      "id": "CMP-1042",
      "currentRevision": { "id": "REV-1042-4", "state": "APPROVED" },
      "approvalStatus": "APPROVED",
      "canSchedule": { "allowed": true },
      "allowedActions": ["SCHEDULE", "VIEW_HISTORY"]
    }
  },
  "meta": {
    "requestId": "req_01JA7Z9P5Q3R7S9T1V3W5X7Y9Z",
    "serverTime": "2026-11-01T11:32:02+05:30"
  }
}
```

---

## 6. Schedule the approved revision

```http
POST /v1/campaigns/CMP-1042/schedule
Idempotency-Key: 019a2f7c-4bfc-726a-9b4d-6e7f8091a2b3
Content-Type: application/json

{
  "revisionId": "REV-1042-4",
  "expectedContentHash": "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4",
  "scheduledStartAt": "2026-11-08T10:00:00+05:30"
}
```

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "data": {
    "schedule": {
      "id": "SCH-7002",
      "campaignId": "CMP-1042",
      "revisionId": "REV-1042-4",
      "approvalDecisionId": "DEC-9003",
      "scheduledStartAt": "2026-11-08T10:00:00+05:30",
      "state": "SCHEDULED"
    },
    "campaign": {
      "id": "CMP-1042",
      "approvalStatus": "APPROVED",
      "scheduleStatus": "SCHEDULED",
      "canSchedule": { "allowed": false, "code": "ALREADY_SCHEDULED" },
      "allowedActions": ["EDIT", "VIEW_HISTORY"]
    }
  },
  "meta": {
    "requestId": "req_01JA7ZA1B2C3D4E5F6G7H8J9K0",
    "serverTime": "2026-11-01T11:35:02+05:30"
  }
}
```

---

## 7. Stale revision conflict

```http
POST /v1/campaigns/CMP-1042/decisions
Idempotency-Key: 019a2f7c-5c0d-737b-8c5e-7f8091a2b3c4
Content-Type: application/json

{
  "revisionId": "REV-1042-3",
  "outcome": "APPROVED",
  "reason": null,
  "expectedContentHash": "7f6e5d4c3b2a1908f7e6d5c4b3a29180f6e5d4c3b2a1908f7e6d5c4b3a291807"
}
```

```http
HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "error": {
    "code": "REVISION_STALE",
    "message": "Revision 3 is no longer current.",
    "details": {
      "currentRevision": {
        "id": "REV-1042-4",
        "revisionNumber": 4,
        "state": "DRAFT"
      }
    },
    "retryable": false
  },
  "meta": {
    "requestId": "req_01JA7Z8N4P2Q6R8S0T2V4W6X8Y",
    "serverTime": "2026-11-01T11:27:14+05:30"
  }
}
```

**Expected database state:** no decision, no audit event, revision 3 remains `SUPERSEDED`.

---

## 8. Idempotent replay

Same request as example 5, same key, sent again after a timeout.

```http
HTTP/1.1 200 OK
Idempotent-Replay: true
Content-Type: application/json

{
  "data": {
    "decision": {
      "id": "DEC-9003",
      "revisionId": "REV-1042-4",
      "outcome": "APPROVED",
      "reviewerId": "USR-REV-1",
      "decidedAt": "2026-11-01T11:32:02+05:30"
    },
    "campaign": {
      "id": "CMP-1042",
      "approvalStatus": "APPROVED",
      "allowedActions": ["SCHEDULE", "VIEW_HISTORY"]
    }
  },
  "meta": {
    "requestId": "req_01JA7Z9P5Q3R7S9T1V3W5X7Y9Z",
    "serverTime": "2026-11-01T11:33:10+05:30"
  }
}
```

The `requestId` is the **original** request’s ID, not the retry’s. That is how the log line and the audit event stay correlated.

---

## 9. Key reuse with a different body

```http
POST /v1/campaigns/CMP-1042/decisions
Idempotency-Key: 019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2
Content-Type: application/json

{
  "revisionId": "REV-1042-4",
  "outcome": "CHANGES_REQUESTED",
  "reason": "Changed my mind about the audience.",
  "expectedContentHash": "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4"
}
```

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "error": {
    "code": "IDEMPOTENCY_KEY_REUSED",
    "message": "This idempotency key was used for a different request.",
    "details": { "endpoint": "POST /v1/campaigns/:id/decisions" },
    "retryable": false
  },
  "meta": {
    "requestId": "req_01JA7ZB2C3D4E5F6G7H8J9K0L1",
    "serverTime": "2026-11-01T11:36:00+05:30"
  }
}
```

A new intent needs a new key.

---

## 10. Reconcile a command

### Completed

```http
GET /v1/commands/019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "state": "COMPLETED",
    "responseStatus": 200,
    "response": {
      "decision": { "id": "DEC-9003", "outcome": "APPROVED" },
      "campaign": { "id": "CMP-1042", "approvalStatus": "APPROVED" }
    }
  },
  "meta": {
    "requestId": "req_01JA7ZB3D4E5F6G7H8J9K0L1M2",
    "serverTime": "2026-11-01T11:33:12+05:30"
  }
}
```

### In progress

```http
HTTP/1.1 202 Accepted
Content-Type: application/json

{
  "data": { "state": "IN_PROGRESS" },
  "meta": { "requestId": "req_01JA7ZB4", "serverTime": "2026-11-01T11:33:12+05:30" }
}
```

### Not found

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "data": { "state": "NOT_FOUND" },
  "meta": { "requestId": "req_01JA7ZB5", "serverTime": "2026-11-01T11:33:12+05:30" }
}
```

`NOT_FOUND` means the key never committed. The client may resend with the same key.

---

## 11. Validation error

```http
POST /v1/campaigns
Idempotency-Key: 019a2f7c-8f1e-7c3a-9b2d-6a4e5f6d7c8b
Content-Type: application/json

{
  "name": "Diwali Reset",
  "objective": "Win back lapsed customers",
  "audience": "",
  "channel": "BILLBOARD",
  "budgetMinor": -100,
  "currency": "INR"
}
```

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The proposal is incomplete.",
    "details": {
      "fields": [
        { "path": "audience", "message": "Audience is required." },
        { "path": "channel", "message": "Channel must be one of INSTAGRAM, EMAIL, SEARCH, DISPLAY, IN_APP." },
        { "path": "budgetMinor", "message": "Budget must be greater than zero." }
      ]
    },
    "retryable": false
  },
  "meta": {
    "requestId": "req_01JA7ZB6",
    "serverTime": "2026-11-01T11:40:00+05:30"
  }
}
```

---

## 12. A marketer cannot decide

The actor is `USR-MKT-1` (Meera). She created `CMP-1042`, and her role is `MARKETER`. The service checks the role before the self-approval guard, so the error is `FORBIDDEN`, not `SELF_APPROVAL_FORBIDDEN`.

```http
POST /v1/campaigns/CMP-1042/decisions
Idempotency-Key: 019a2f7c-6d1e-748c-9d6f-8091a2b3c4d5
Content-Type: application/json

{
  "revisionId": "REV-1042-4",
  "outcome": "APPROVED",
  "reason": null,
  "expectedContentHash": "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4"
}
```

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "error": {
    "code": "FORBIDDEN",
    "message": "Only a reviewer can decide on a campaign.",
    "details": { "requiredRole": "REVIEWER" },
    "retryable": false
  },
  "meta": {
    "requestId": "req_01JA7ZB7",
    "serverTime": "2026-11-01T11:41:00+05:30"
  }
}
```

The narrower `SELF_APPROVAL_FORBIDDEN` guard applies when a reviewer is also the campaign creator. The canonical campaign is created by Meera, so that case is exercised by test T-15 with a separate fixture, not with `CMP-1042`.

---

## Envelope notes

- `meta.requestId` is generated or accepted by the server and echoed in every log line.
- `meta.serverTime` is the authoritative clock for the response.
- Error `details` is intentionally small. The client should not parse free-text messages for control flow; it should switch on `code`.
- `Idempotent-Replay: true` is present only on a replay.
- A `201` on schedule is a new schedule. A `200` on a replayed schedule is the same schedule.
