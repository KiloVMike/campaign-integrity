# Campaign Integrity

**MAL 4 · Martech track · Architecture submission**

> The campaign that gets scheduled is the campaign that was approved.

---

## Read this first

This is an **architecture-first submission**, not a working prototype. It contains the brief, high-level design, focused low-level design, three ADRs, walkthroughs, verification plan, and presentation material.

- **No application code is included.**
- **Test cases are specified, not executed.** They are written so they can be implemented directly.
- **All log lines, API responses, and identifiers are illustrative examples**, not captured output.
- Simulated behaviour is labelled as such. The design does not claim guarantees that have not been verified.

The MAL 4 brief explicitly allows this: working code and polished UI are optional, while architecture, evidence, and the ability to defend decisions carry the score.

---

## The problem in one paragraph

Marketing teams coordinate approvals through email, chat, and spreadsheets. Approval is usually recorded as a status on a campaign, not as a decision about a specific version of its content. When a marketer changes the budget or audience after approval, the status can remain “Approved” and an unreviewed campaign can be scheduled. The risk is not that the status is missing; it is that the status is **detached from the content it was meant to authorise**.

## The solution

**Campaign Integrity** binds every approval decision to an immutable campaign revision and a content hash. Scheduling is a server-enforced transaction that succeeds only when:

1. the requested revision is the campaign’s **current** revision;
2. that revision has an **APPROVED** decision;
3. the decision’s content hash matches the revision’s content hash; and
4. no active schedule already exists.

Any edit to a submitted or approved proposal creates a new revision. The previous approval remains in history but is no longer valid for scheduling. Editing a scheduled campaign automatically cancels the schedule in the same transaction, so an active schedule can never point at content that is no longer approved.

## The invariant

```
active_schedule(c)
  ⇒ current_revision(c).state = APPROVED
  ∧ decision.revision_id       = current_revision(c).id
  ∧ decision.content_hash      = current_revision(c).content_hash
```

This single invariant is enforced in the database transaction, in the domain rules, and in the API contract. Everything else in the design exists to keep it true under edits, retries, concurrency, and restarts.

---

## Deliverables map

| MAL 4 deliverable | File | What it contains | Rubric weight |
|---|---|---|---|
| One-page solution brief | [`01-solution-brief.md`](01-solution-brief.md) | Users, problem, core journey, scope, assumptions, constraints, success conditions | 10% framing |
| High-level design | [`02-high-level-design.md`](02-high-level-design.md) | Components, responsibilities, dependencies, data flows, source of truth, trade-offs | 15% structure |
| Low-level design and critical feature | [`03-low-level-design.md`](03-low-level-design.md) | Modules, interfaces, models, state machine, scheduling transaction, schema, API, idempotency | 15% data/state + 10% failure |
| Three ADRs | [`04-adrs/`](04-adrs/) | Revision-bound approvals; server authority + outbox; idempotent commands + audit | 10% trade-offs |
| Core, failure, and change walkthroughs | [`05-walkthroughs/`](05-walkthroughs/) | End-to-end journey; lost response and stale revision; dual-approval change | 15% core journey + 10% failure |
| Verification and diagnostics | [`06-verification-and-diagnostics.md`](06-verification-and-diagnostics.md) | Test matrix, example inputs/outcomes, log schema, metrics, investigation runbook | 15% verification |
| Presentation and defence | [`07-presentation.md`](07-presentation.md), [`08-walkthrough-script.md`](08-walkthrough-script.md), [`09-judge-qa.md`](09-judge-qa.md) | 8-slide narrative, 6-minute walkthrough, likely questions and answers | 10% defence |
| Supporting evidence | [`evidence/`](evidence/) | Seed data, API examples, illustrative logs | Supports all |

---

## The 60-second pitch

> An approval is not a status. It is a claim about a specific piece of content.
>
> We bind every approval to an immutable revision and a content hash. A campaign can be scheduled only if the revision being scheduled is the exact revision that was approved. Change the budget or audience, and the approval is no longer valid — automatically.
>
> The hard part is not the button. It is keeping that guarantee true when a reviewer approves an outdated revision, when a response is lost after the server committed, when the app is killed mid-request, and when two people act at once.
>
> We enforce the rule in one database transaction, make every command idempotent, keep an append-only audit trail, and show the user the difference between “pending” and “approved”. The design is deliberately small: a modular monolith, two roles, and three ADRs that defend the choices that matter.

---

## Core journey

| # | Actor | Action | Result |
|---|---|---|---|
| 1 | Marketer | Creates a campaign proposal | Revision 1 in `DRAFT` |
| 2 | Marketer | Submits for review | Revision 1 in `IN_REVIEW` |
| 3 | Reviewer | Requests changes with a reason | Revision 1 in `CHANGES_REQUESTED` |
| 4 | Marketer | Revises budget/audience | Revision 2 in `DRAFT`; revision 1 `SUPERSEDED` |
| 5 | Marketer | Resubmits | Revision 2 in `IN_REVIEW` |
| 6 | Reviewer | Approves revision 2 | Revision 2 `APPROVED`; decision bound to its hash |
| 7 | Marketer | Schedules for 8 Nov, 10:00 | Schedule `SCHEDULED`; both users see the status |
| 8 | Marketer | Edits the budget after scheduling | Revision 3 `DRAFT`; approval invalid; schedule auto-cancelled |

The full narrative, with timestamps and expected UI states, is in [`05-walkthroughs/core-journey.md`](05-walkthroughs/core-journey.md).

---

## Design at a glance

| Decision | Choice | Why |
|---|---|---|
| Unit of approval | Immutable campaign revision | An approval must name the content it authorises |
| Approval record | `revision_id` + `content_hash` | Detects both stale revisions and in-place mutation |
| Approval status | Derived from current revision + decision | A stored boolean can drift; a derivation cannot |
| Source of truth | PostgreSQL on the server | One authority for state transitions and audit |
| Client role | Read cache + command outbox | Fast UI without split-brain |
| Retries | Client-generated idempotency keys | A timeout is not evidence of failure |
| Audit | Append-only, written in the same transaction | State and evidence cannot disagree |
| Backend shape | Modular monolith | Transactions and constraints matter more than service count |
| v1 approver model | One authorised reviewer, no self-approval | Small scope; dual approval is the change scenario |

---

## Repository map

```
MAL Hackathon/
├── README.md
├── 01-solution-brief.md
├── 02-high-level-design.md
├── 03-low-level-design.md
├── 04-adrs/
│   ├── ADR-001-revision-bound-approvals.md
│   ├── ADR-002-server-authority-and-outbox.md
│   └── ADR-003-idempotent-commands-and-audit.md
├── 05-walkthroughs/
│   ├── core-journey.md
│   ├── failure-and-recovery.md
│   └── requirement-change.md
├── 06-verification-and-diagnostics.md
├── 07-presentation.md
├── 08-walkthrough-script.md
├── 09-judge-qa.md
└── evidence/
    ├── sample-data.md
    ├── api-examples.md
    └── sample-logs.md
```

---

## Submission checklist

- [x] One-page solution brief
- [x] High-level design with components, responsibilities, dependencies, data flows, and source of truth
- [x] Low-level design with interfaces, models, states, and a detailed critical-feature walkthrough
- [x] Three ADRs with context, alternatives, decision, consequences, and revisit triggers
- [x] Core journey walkthrough
- [x] Failure and recovery walkthrough
- [x] Realistic requirement-change walkthrough
- [x] Verification plan, example inputs and outcomes, diagnostics, and investigation runbook
- [x] Presentation outline and architecture-defence Q&A

---

## How to use this pack

1. **Read `01` and `02` first.** They establish the problem, scope, and shape of the system.
2. **Use `03` for the technical defence.** It contains the state machine, schema, transaction, and API contracts.
3. **Rehearse with `08`.** It is a timed, six-minute structured walkthrough that does not require a prototype.
4. **Prepare for questions with `09`.** It covers the likely challenges, including the ones that expose weak designs.
5. **Keep the honesty note visible.** If asked what is verified, say plainly: “The design is complete; the tests are specified, not executed. These logs are illustrative.”

The closing line for the presentation:

> **Small enough to finish. Explicit enough to defend.**
