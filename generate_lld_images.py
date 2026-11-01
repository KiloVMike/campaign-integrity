import os
import subprocess
import sys

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

BASE_CSS = """
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background-color: #080c14;
    background-image: 
      radial-gradient(circle at 10% 15%, rgba(59, 130, 246, 0.09) 0%, transparent 40%),
      radial-gradient(circle at 90% 85%, rgba(16, 185, 129, 0.08) 0%, transparent 40%),
      linear-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 24px 24px, 24px 24px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #f1f5f9;
    padding: 24px 32px;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.12);
    margin-bottom: 16px;
  }
  .title-group h1 {
    font-size: 21pt;
    font-weight: 850;
    letter-spacing: -0.5px;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .title-group h1 .tag {
    font-size: 9pt;
    font-weight: 700;
    color: #38bdf8;
    background: rgba(14, 165, 233, 0.18);
    border: 1px solid rgba(56, 189, 248, 0.35);
    padding: 3px 9px;
    border-radius: 5px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
  }
  .title-group p {
    font-size: 10pt;
    color: #94a3b8;
    margin-top: 3px;
    font-weight: 500;
  }
  .meta-badges {
    text-align: right;
    display: flex;
    gap: 8px;
  }
  .meta-badge {
    background: rgba(15,23,42,0.85);
    border: 1px solid rgba(255,255,255,0.12);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 8pt;
    color: #cbd5e1;
    font-weight: 600;
  }
  .meta-badge.highlight {
    background: rgba(14, 165, 233, 0.25);
    border-color: #0ea5e9;
    color: #7dd3fc;
  }
  .card {
    background: rgba(15, 23, 42, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    backdrop-filter: blur(12px);
  }
  .card-title {
    font-size: 9.8pt;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #94a3b8;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    padding-bottom: 6px;
  }
  .card-title .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #0ea5e9;
    display: inline-block;
  }
  .footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 14px;
    padding-top: 10px;
    border-top: 1px solid rgba(255,255,255,0.1);
    font-size: 8.5pt;
    color: #64748b;
  }
  .code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
  }
"""

# ==============================================================================
# LLD 1: DOMAIN ENTITIES & RELATIONAL SCHEMA
# ==============================================================================
html_lld1 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  {BASE_CSS}
  .schema-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }}
  .table-card {{
    background: rgba(15, 23, 42, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    overflow: hidden;
  }}
  .table-card.pk-blue {{ border-top: 3px solid #38bdf8; }}
  .table-card.pk-green {{ border-top: 3px solid #34d399; }}
  .table-card.pk-purple {{ border-top: 3px solid #a78bfa; }}
  .table-card.pk-amber {{ border-top: 3px solid #fbbf24; }}
  .table-card.pk-rose {{ border-top: 3px solid #f43f5e; }}
  .table-header {{
    background: rgba(30, 41, 59, 0.7);
    padding: 8px 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255,255,255,0.08);
  }}
  .table-name {{
    font-family: monospace;
    font-weight: 850;
    font-size: 9.5pt;
    color: #ffffff;
  }}
  .table-desc {{
    font-size: 7.5pt;
    color: #94a3b8;
  }}
  .column-list {{
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-family: monospace;
    font-size: 8pt;
  }}
  .col-row {{
    display: flex;
    justify-content: space-between;
    color: #cbd5e1;
    border-bottom: 1px dashed rgba(255,255,255,0.05);
    padding-bottom: 2px;
  }}
  .col-name {{ color: #e2e8f0; font-weight: 600; }}
  .col-name.pk {{ color: #38bdf8; font-weight: bold; }}
  .col-name.fk {{ color: #a78bfa; }}
  .col-type {{ color: #64748b; font-size: 7.5pt; }}
  .constraint-box {{
    background: rgba(0,0,0,0.25);
    padding: 6px 10px;
    font-size: 7.5pt;
    color: #94a3b8;
    border-top: 1px solid rgba(255,255,255,0.06);
    line-height: 1.25;
  }}
  .constraint-box strong {{ color: #38bdf8; }}
</style>
</head>
<body style="width: 1600px; height: 800px;">
  <div class="header">
    <div class="title-group">
      <h1>LLD Diagram 01: Relational Schema & Relational Invariants <span class="tag">Database Architecture</span></h1>
      <p>PostgreSQL System of Record DDL, Foreign Key Constraints & Row-Lock Targets</p>
    </div>
    <div class="meta-badges">
      <div class="meta-badge highlight">PostgreSQL 16</div>
      <div class="meta-badge">Append-Only Audit</div>
      <div class="meta-badge">LLD Section 5</div>
    </div>
  </div>

  <div class="schema-grid">
    <!-- TABLE 1: CAMPAIGNS -->
    <div class="table-card pk-blue">
      <div class="table-header">
        <span class="table-name">campaigns</span>
        <span class="table-desc">Campaign Container & Lock Root</span>
      </div>
      <div class="column-list">
        <div class="col-row"><span class="col-name pk">id (PK)</span><span class="col-type">TEXT (CMP-...)</span></div>
        <div class="col-row"><span class="col-name">created_by</span><span class="col-type">TEXT NOT NULL</span></div>
        <div class="col-row"><span class="col-name fk">current_rev_id (FK)</span><span class="col-type">TEXT NOT NULL</span></div>
        <div class="col-row"><span class="col-name">created_at</span><span class="col-type">TIMESTAMPTZ NOT NULL</span></div>
        <div class="col-row"><span class="col-name">updated_at</span><span class="col-type">TIMESTAMPTZ NOT NULL</span></div>
      </div>
      <div class="constraint-box">
        <strong>Lock Target:</strong> Serializes concurrency via <code>SELECT * FROM campaigns FOR UPDATE</code>.
      </div>
    </div>

    <!-- TABLE 2: REVISIONS -->
    <div class="table-card pk-green">
      <div class="table-header">
        <span class="table-name">revisions</span>
        <span class="table-desc">Immutable Version Tree</span>
      </div>
      <div class="column-list">
        <div class="col-row"><span class="col-name pk">id (PK)</span><span class="col-type">TEXT (REV-...)</span></div>
        <div class="col-row"><span class="col-name fk">campaign_id (FK)</span><span class="col-type">TEXT NOT NULL</span></div>
        <div class="col-row"><span class="col-name">revision_number</span><span class="col-type">INTEGER NOT NULL</span></div>
        <div class="col-row"><span class="col-name">state</span><span class="col-type">RevisionState ENUM</span></div>
        <div class="col-row"><span class="col-name">objective, audience</span><span class="col-type">TEXT NOT NULL</span></div>
        <div class="col-row"><span class="col-name">channel, budget_paise</span><span class="col-type">ENUM, BIGINT</span></div>
        <div class="col-row"><span class="col-name">content_hash</span><span class="col-type">CHAR(64) SHA-256</span></div>
      </div>
      <div class="constraint-box">
        <strong>Copy-on-Write:</strong> Edits insert a new row; prior revision marked <code>SUPERSEDED</code>.
      </div>
    </div>

    <!-- TABLE 3: DECISIONS -->
    <div class="table-card pk-purple">
      <div class="table-header">
        <span class="table-name">decisions</span>
        <span class="table-desc">Cryptographically Bound Approval</span>
      </div>
      <div class="column-list">
        <div class="col-row"><span class="col-name pk">id (PK)</span><span class="col-type">TEXT (DEC-...)</span></div>
        <div class="col-row"><span class="col-name fk">campaign_id (FK)</span><span class="col-type">TEXT NOT NULL</span></div>
        <div class="col-row"><span class="col-name fk">revision_id (FK)</span><span class="col-type">TEXT NOT NULL</span></div>
        <div class="col-row"><span class="col-name">reviewer_id</span><span class="col-type">TEXT NOT NULL</span></div>
        <div class="col-row"><span class="col-name">outcome</span><span class="col-type">APPROVED | CHANGES_REQ</span></div>
        <div class="col-row"><span class="col-name">content_hash</span><span class="col-type">CHAR(64) SHA-256</span></div>
        <div class="col-row"><span class="col-name">note</span><span class="col-type">TEXT (Required if changes)</span></div>
      </div>
      <div class="constraint-box">
        <strong>Derived Approval:</strong> Valid iff <code>rev.id = dec.rev_id ∧ rev.hash = dec.hash</code>.
      </div>
    </div>

    <!-- TABLE 4: SCHEDULES -->
    <div class="table-card pk-amber">
      <div class="table-header">
        <span class="table-name">schedules</span>
        <span class="table-desc">Atomic Eligibility Gate Target</span>
      </div>
      <div class="column-list">
        <div class="col-row"><span class="col-name pk">id (PK)</span><span class="col-type">TEXT (SCH-...)</span></div>
        <div class="col-row"><span class="col-name fk">campaign_id (FK)</span><span class="col-type">TEXT NOT NULL</span></div>
        <div class="col-row"><span class="col-name fk">revision_id (FK)</span><span class="col-type">TEXT NOT NULL</span></div>
        <div class="col-row"><span class="col-name fk">decision_id (FK)</span><span class="col-type">TEXT NOT NULL</span></div>
        <div class="col-row"><span class="col-name">state</span><span class="col-type">SCHEDULED | CANCELLED</span></div>
        <div class="col-row"><span class="col-name">scheduled_at</span><span class="col-type">TIMESTAMPTZ NOT NULL</span></div>
      </div>
      <div class="constraint-box">
        <strong>Partial Unique Index:</strong> Exactly one active <code>SCHEDULED</code> row per campaign allowed.
      </div>
    </div>

    <!-- TABLE 5: AUDIT_EVENTS -->
    <div class="table-card pk-rose">
      <div class="table-header">
        <span class="table-name">audit_events</span>
        <span class="table-desc">Tamper-Evident Domain Trail</span>
      </div>
      <div class="column-list">
        <div class="col-row"><span class="col-name pk">id (PK)</span><span class="col-type">TEXT (AUD-...)</span></div>
        <div class="col-row"><span class="col-name">actor_id</span><span class="col-type">TEXT NOT NULL</span></div>
        <div class="col-row"><span class="col-name">event_type</span><span class="col-type">AuditEventType ENUM</span></div>
        <div class="col-row"><span class="col-name fk">campaign_id, rev_id</span><span class="col-type">TEXT NOT NULL</span></div>
        <div class="col-row"><span class="col-name">correlation_id</span><span class="col-type">UUID NOT NULL</span></div>
        <div class="col-row"><span class="col-name">payload</span><span class="col-type">JSONB NOT NULL</span></div>
        <div class="col-row"><span class="col-name">created_at</span><span class="col-type">TIMESTAMPTZ DEFAULT now()</span></div>
      </div>
      <div class="constraint-box">
        <strong>Insert-Only:</strong> Database permissions revoke <code>UPDATE</code> and <code>DELETE</code>.
      </div>
    </div>

    <!-- TABLE 6: IDEMPOTENCY_KEYS -->
    <div class="table-card pk-blue">
      <div class="table-header">
        <span class="table-name">idempotency_keys</span>
        <span class="table-desc">Crash & Replay Defense</span>
      </div>
      <div class="column-list">
        <div class="col-row"><span class="col-name pk">key (PK)</span><span class="col-type">TEXT (UUID)</span></div>
        <div class="col-row"><span class="col-name">actor_id</span><span class="col-type">TEXT NOT NULL</span></div>
        <div class="col-row"><span class="col-name">request_hash</span><span class="col-type">CHAR(64) SHA-256</span></div>
        <div class="col-row"><span class="col-name">status</span><span class="col-type">IN_FLIGHT | COMMITTED</span></div>
        <div class="col-row"><span class="col-name">response_status</span><span class="col-type">INTEGER</span></div>
        <div class="col-row"><span class="col-name">response_body</span><span class="col-type">JSONB</span></div>
        <div class="col-row"><span class="col-name">expires_at</span><span class="col-type">TIMESTAMPTZ NOT NULL</span></div>
      </div>
      <div class="constraint-box">
        <strong>Exactly-Once:</strong> Duplicate requests return cached response body directly.
      </div>
    </div>
  </div>

  <div class="footer">
    <div><strong>Referential Integrity:</strong> All revision references are immutable foreign keys. Deleting active campaigns is prohibited.</div>
    <div>Relational Schema Blueprint · Low-Level Design Section 5</div>
  </div>
</body>
</html>
"""

# ==============================================================================
# LLD 2: FINITE STATE MACHINE & COPY-ON-WRITE LIFECYCLE
# ==============================================================================
html_lld2 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  {BASE_CSS}
  .fsm-canvas {{
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 18px;
  }}
  .state-flow-box {{
    background: rgba(15, 23, 42, 0.85);
    border: 1.5px solid #0ea5e9;
    border-radius: 12px;
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    box-shadow: 0 0 30px rgba(14, 165, 233, 0.12);
  }}
  .states-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }}
  .state-node {{
    background: rgba(30, 41, 59, 0.9);
    border: 1.5px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    padding: 12px 14px;
    text-align: center;
    flex: 1;
  }}
  .state-node.draft {{ border-color: #94a3b8; }}
  .state-node.review {{ border-color: #38bdf8; background: rgba(14, 165, 233, 0.15); }}
  .state-node.changes {{ border-color: #fbbf24; background: rgba(245, 158, 11, 0.15); }}
  .state-node.approved {{ border-color: #34d399; background: rgba(16, 185, 129, 0.15); }}
  .state-node.scheduled {{ border-color: #a78bfa; background: rgba(139, 92, 246, 0.15); }}
  .state-node.superseded {{ border-color: #f43f5e; background: rgba(244, 63, 94, 0.15); }}
  .state-title {{ font-size: 10.5pt; font-weight: 850; color: #ffffff; margin-bottom: 3px; }}
  .state-desc {{ font-size: 7.5pt; color: #94a3b8; line-height: 1.2; }}
  .fsm-arrow {{ color: #38bdf8; font-weight: bold; font-size: 14pt; }}
  
  .transitions-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 8pt;
    margin-top: 6px;
  }}
  .transitions-table th {{
    background: rgba(30, 41, 59, 0.6);
    color: #94a3b8;
    text-align: left;
    padding: 6px 8px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    font-size: 7.5pt;
    text-transform: uppercase;
  }}
  .transitions-table td {{
    padding: 6px 8px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    color: #cbd5e1;
  }}
  .guard-badge {{
    background: rgba(14, 165, 233, 0.2);
    color: #38bdf8;
    padding: 2px 5px;
    border-radius: 3px;
    font-family: monospace;
    font-size: 7.2pt;
  }}
  .cow-banner {{
    background: linear-gradient(90deg, rgba(244, 63, 94, 0.15) 0%, rgba(15, 23, 42, 0.8) 100%);
    border-left: 3px solid #f43f5e;
    padding: 10px 14px;
    border-radius: 4px;
    font-size: 8.5pt;
    color: #f1f5f9;
  }}
  .cow-banner strong {{ color: #fb7185; }}
  .sidebar-cards {{ display: flex; flex-direction: column; gap: 14px; }}
  .side-card {{
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 12px 14px;
  }}
  .side-card h4 {{ font-size: 9.5pt; color: #38bdf8; margin-bottom: 6px; }}
  .side-card p {{ font-size: 8.2pt; color: #94a3b8; line-height: 1.35; }}
</style>
</head>
<body style="width: 1600px; height: 800px;">
  <div class="header">
    <div class="title-group">
      <h1>LLD Diagram 02: Revision State Machine & Copy-on-Write <span class="tag">Finite State Machine</span></h1>
      <p>Deterministic Lifecycle Transitions, Guard Conditions & Mutation Invalidation</p>
    </div>
    <div class="meta-badges">
      <div class="meta-badge highlight">Pure Domain State Machine</div>
      <div class="meta-badge">LLD Section 3</div>
    </div>
  </div>

  <div class="fsm-canvas">
    <div class="state-flow-box">
      <div class="card-title"><span class="dot"></span> Revision Lifecycle States</div>
      <div class="states-row">
        <div class="state-node draft">
          <div class="state-title">DRAFT</div>
          <div class="state-desc">Authoring proposal. Editable.</div>
        </div>
        <span class="fsm-arrow">➔</span>
        <div class="state-node review">
          <div class="state-title">IN_REVIEW</div>
          <div class="state-desc">Locked. Awaiting decision.</div>
        </div>
        <span class="fsm-arrow">➔</span>
        <div class="state-node changes">
          <div class="state-title">CHANGES_REQ</div>
          <div class="state-desc">Feedback provided.</div>
        </div>
        <span class="fsm-arrow">➔</span>
        <div class="state-node approved">
          <div class="state-title">APPROVED</div>
          <div class="state-desc">Bound to SHA-256 hash.</div>
        </div>
      </div>

      <div class="cow-banner">
        <strong>Copy-on-Write Mutation Rule:</strong> When an APPROVED or IN_REVIEW revision is edited, the server marks the revision <code>SUPERSEDED</code>, inserts a fresh <code>DRAFT</code> revision, and automatically cancels any active schedule in the same atomic transaction.
      </div>

      <div class="card-title" style="margin-top: 4px;"><span class="dot"></span> Enforced Transition Matrix</div>
      <table class="transitions-table">
        <thead>
          <tr>
            <th>From State</th>
            <th>Trigger Action</th>
            <th>To State</th>
            <th>Guard Condition</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>DRAFT</code></td>
            <td>Submit for Review</td>
            <td><code>IN_REVIEW</code></td>
            <td><span class="guard-badge">all_fields_present ∧ author_role</span></td>
          </tr>
          <tr>
            <td><code>IN_REVIEW</code></td>
            <td>Reviewer Approves</td>
            <td><code>APPROVED</code></td>
            <td><span class="guard-badge">reviewer ≠ author ∧ hash_match</span></td>
          </tr>
          <tr>
            <td><code>IN_REVIEW</code></td>
            <td>Request Changes</td>
            <td><code>CHANGES_REQUESTED</code></td>
            <td><span class="guard-badge">reviewer ≠ author ∧ note.length &gt; 0</span></td>
          </tr>
          <tr>
            <td><code>CHANGES_REQUESTED</code></td>
            <td>Revise Proposal</td>
            <td><code>DRAFT (rev + 1)</code></td>
            <td><span class="guard-badge">copy_on_write ∧ rev_superseded</span></td>
          </tr>
          <tr>
            <td><code>APPROVED</code></td>
            <td>Schedule Campaign</td>
            <td><code>SCHEDULED</code></td>
            <td><span class="guard-badge">atomic_invariant_gate_passed</span></td>
          </tr>
          <tr>
            <td><code>APPROVED</code></td>
            <td>Post-Approval Edit</td>
            <td><code>SUPERSEDED ➔ DRAFT</code></td>
            <td><span class="guard-badge">cancel_schedule ∧ new_rev_fork</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="sidebar-cards">
      <div class="side-card">
        <h4>Derived State Principle</h4>
        <p>A campaign does not possess an <code>is_approved</code> boolean column. Approval is derived dynamically from <code>(current_rev, active_decision, matching_hash)</code>. If content changes, the hash changes, invalidating approval instantly without background sync.</p>
      </div>

      <div class="side-card">
        <h4>Materiality in Version 1</h4>
        <p>Every proposal field (<code>objective</code>, <code>audience</code>, <code>channel</code>, <code>budget_paise</code>) is strictly material. Any modification whatsoever invalidates the content hash and requires full reviewer re-evaluation.</p>
      </div>

      <div class="side-card">
        <h4>Zero Split-Brain</h4>
        <p>The client mobile app never advances state optimistically. While a command is in-flight, it shows a "Confirming..." banner. Authority resides exclusively with PostgreSQL transaction commits.</p>
      </div>
    </div>
  </div>

  <div class="footer">
    <div><strong>Deterministic Lifecycle:</strong> Unapproved states cannot transition to SCHEDULED. Stale approvals yield 409 Conflict.</div>
    <div>State Machine Blueprint · Low-Level Design Section 3</div>
  </div>
</body>
</html>
"""

# ==============================================================================
# LLD 3: CRITICAL FEATURE - ATOMIC SCHEDULING TRANSACTION
# ==============================================================================
html_lld3 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  {BASE_CSS}
  .tx-canvas {{
    display: grid;
    grid-template-columns: 1.8fr 1.2fr;
    gap: 18px;
  }}
  .tx-steps-box {{
    background: rgba(15, 23, 42, 0.85);
    border: 1.5px solid #10b981;
    border-radius: 12px;
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    box-shadow: 0 0 30px rgba(16, 185, 129, 0.12);
  }}
  .step-block {{
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 9px 12px;
  }}
  .step-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }}
  .step-idx {{
    font-size: 8pt;
    font-weight: 850;
    color: #34d399;
    text-transform: uppercase;
  }}
  .step-code {{
    font-family: monospace;
    font-size: 8.2pt;
    color: #e2e8f0;
  }}
  .step-desc {{
    font-size: 7.8pt;
    color: #94a3b8;
    line-height: 1.25;
  }}
  .err-pill {{
    background: rgba(244, 63, 94, 0.2);
    color: #fb7185;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 7.2pt;
    font-family: monospace;
    border: 1px solid rgba(244, 63, 94, 0.3);
  }}
  .code-viewer {{
    background: #050811;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 14px 16px;
    font-family: "SFMono-Regular", Consolas, Menlo, monospace;
    font-size: 7.8pt;
    color: #cbd5e1;
    line-height: 1.4;
    overflow: hidden;
  }}
  .kwd {{ color: #f43f5e; font-weight: bold; }}
  .fn {{ color: #38bdf8; }}
  .str {{ color: #34d399; }}
  .cmnt {{ color: #64748b; font-style: italic; }}
</style>
</head>
<body style="width: 1600px; height: 800px;">
  <div class="header">
    <div class="title-group">
      <h1>LLD Diagram 03: Critical Feature — Atomic Scheduling Transaction <span class="tag">Zero Race Windows</span></h1>
      <p>Single PostgreSQL Transaction under Exclusive Row Lock (SELECT ... FOR UPDATE)</p>
    </div>
    <div class="meta-badges">
      <div class="meta-badge highlight">PostgreSQL ACID Gate</div>
      <div class="meta-badge">LLD Section 4</div>
    </div>
  </div>

  <div class="tx-canvas">
    <!-- STEP BY STEP EXECUTION -->
    <div class="tx-steps-box">
      <div class="card-title"><span class="dot"></span> Transaction Execution Pipeline</div>

      <div class="step-block">
        <div class="step-head">
          <span class="step-idx">Phase 1: Claim Idempotency Key</span>
          <span class="step-code">INSERT INTO idempotency_keys</span>
        </div>
        <div class="step-desc">Claim key in <code>IN_FLIGHT</code> state. If key already exists with committed response, return cached response immediately.</div>
      </div>

      <div class="step-block" style="border-left: 3px solid #38bdf8;">
        <div class="step-head">
          <span class="step-idx">Phase 2: Acquire Row-Lock</span>
          <span class="step-code">SELECT * FROM campaigns WHERE id = $1 FOR UPDATE</span>
        </div>
        <div class="step-desc">Locks campaign row exclusively. Serializes all concurrent review, edit, and schedule attempts across all API instances.</div>
      </div>

      <div class="step-block">
        <div class="step-head">
          <span class="step-idx">Phase 3: Four Invariant Assertions</span>
          <span class="err-pill">ROLLBACK ON FAILURE</span>
        </div>
        <div class="step-desc">
          1. <strong>Current Revision:</strong> <code>req.revisionId == campaign.current_revision_id</code> (else <code>409 REVISION_STALE</code>)<br/>
          2. <strong>Approved State:</strong> <code>current_revision.state == APPROVED</code> (else <code>409 APPROVAL_INVALID</code>)<br/>
          3. <strong>Cryptographic Hash:</strong> <code>decision.content_hash == current_revision.content_hash</code> (else <code>409 HASH_MISMATCH</code>)<br/>
          4. <strong>Schedule Uniqueness:</strong> No active schedule exists (else <code>409 ALREADY_SCHEDULED</code>)
        </div>
      </div>

      <div class="step-block" style="border-left: 3px solid #10b981;">
        <div class="step-head">
          <span class="step-idx">Phase 4: Atomic Commit</span>
          <span class="step-code">INSERT schedule + audit + COMMIT</span>
        </div>
        <div class="step-desc">Inserts schedule row, emits <code>CAMPAIGN_SCHEDULED</code> audit event, stores response in idempotency table, and commits transaction.</div>
      </div>
    </div>

    <!-- CODE VIEW -->
    <div class="code-viewer">
<span class="cmnt">// ScheduleService.execute(command, context)</span>
<span class="kwd">await</span> pg.transaction(<span class="kwd">async</span> (client) => {{
  <span class="cmnt">// 1. Lock campaign root row</span>
  <span class="kwd">const</span> campaign = <span class="kwd">await</span> client.query(
    <span class="str">"SELECT * FROM campaigns WHERE id = $1 FOR UPDATE"</span>,
    [cmd.campaignId]
  );

  <span class="cmnt">// 2. Check 1: Must be current revision</span>
  <span class="kwd">if</span> (cmd.revisionId !== campaign.current_revision_id) {{
    <span class="kwd">throw new</span> <span class="fn">ConflictError</span>(<span class="str">"REVISION_STALE"</span>);
  }}

  <span class="cmnt">// 3. Check 2 & 3: Approved state & Hash match</span>
  <span class="kwd">const</span> rev = <span class="kwd">await</span> getRevision(client, cmd.revisionId);
  <span class="kwd">const</span> dec = <span class="kwd">await</span> getActiveDecision(client, rev.id);
  <span class="kwd">if</span> (rev.state !== <span class="str">"APPROVED"</span>) {{
    <span class="kwd">throw new</span> <span class="fn">ConflictError</span>(<span class="str">"APPROVAL_INVALID"</span>);
  }}
  <span class="kwd">if</span> (dec.content_hash !== rev.content_hash) {{
    <span class="kwd">throw new</span> <span class="fn">ConflictError</span>(<span class="str">"CONTENT_HASH_MISMATCH"</span>);
  }}

  <span class="cmnt">// 4. Check 4: Schedule uniqueness</span>
  <span class="kwd">if</span> (<span class="kwd">await</span> hasActiveSchedule(client, campaign.id)) {{
    <span class="kwd">throw new</span> <span class="fn">ConflictError</span>(<span class="str">"ALREADY_SCHEDULED"</span>);
  }}

  <span class="cmnt">// 5. Persist schedule + audit atomically</span>
  <span class="kwd">await</span> insertSchedule(client, ...);
  <span class="kwd">await</span> insertAudit(client, ...);
}});
    </div>
  </div>

  <div class="footer">
    <div><strong>Core Architectural Invariant:</strong> active_schedule(c) ⇒ current_rev.state = APPROVED ∧ decision.hash = current_rev.hash.</div>
    <div>Atomic Gate Blueprint · Low-Level Design Section 4</div>
  </div>
</body>
</html>
"""

# ==============================================================================
# LLD 4: API CONTRACTS, ERROR ENVELOPES & OUTBOX SYNC
# ==============================================================================
html_lld4 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  {BASE_CSS}
  .api-grid {{
    display: grid;
    grid-template-columns: 1.3fr 1fr;
    gap: 18px;
  }}
  .endpoint-card {{
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 10px;
  }}
  .endpoint-head {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: monospace;
    font-size: 8.8pt;
    font-weight: 700;
  }}
  .method-post {{ background: rgba(59, 130, 246, 0.25); color: #60a5fa; padding: 2px 6px; border-radius: 4px; }}
  .method-patch {{ background: rgba(245, 158, 11, 0.25); color: #fbbf24; padding: 2px 6px; border-radius: 4px; }}
  .method-get {{ background: rgba(16, 185, 129, 0.25); color: #34d399; padding: 2px 6px; border-radius: 4px; }}
  .endpoint-desc {{
    font-size: 7.8pt;
    color: #94a3b8;
    margin-top: 4px;
    line-height: 1.25;
  }}
  .error-tax-box {{
    background: rgba(15, 23, 42, 0.85);
    border: 1.5px solid #f43f5e;
    border-radius: 10px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .err-row {{
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(244, 63, 94, 0.2);
    border-radius: 6px;
    padding: 8px 10px;
  }}
  .err-code {{ font-family: monospace; font-size: 8.5pt; color: #fb7185; font-weight: 700; }}
  .err-meaning {{ font-size: 7.8pt; color: #cbd5e1; margin-top: 2px; }}
</style>
</head>
<body style="width: 1600px; height: 800px;">
  <div class="header">
    <div class="title-group">
      <h1>LLD Diagram 04: API Contracts & Error Taxonomy <span class="tag">RESTful Protocols</span></h1>
      <p>Idempotency Headers, Command Payloads & Deterministic 409 Conflict Responses</p>
    </div>
    <div class="meta-badges">
      <div class="meta-badge highlight">RFC 7807 Error Envelope</div>
      <div class="meta-badge">LLD Section 6 & 7</div>
    </div>
  </div>

  <div class="api-grid">
    <div>
      <div class="endpoint-card">
        <div class="endpoint-head">
          <span class="method-post">POST</span>
          <span>/v1/campaigns</span>
        </div>
        <div class="endpoint-desc">Creates campaign container + Revision 1 (DRAFT). Requires <code>Idempotency-Key</code> header.</div>
      </div>

      <div class="endpoint-card">
        <div class="endpoint-head">
          <span class="method-post">POST</span>
          <span>/v1/campaigns/:id/submit</span>
        </div>
        <div class="endpoint-desc">Locks revision and moves to <code>IN_REVIEW</code>. Computes initial canonical SHA-256 content hash.</div>
      </div>

      <div class="endpoint-card">
        <div class="endpoint-head">
          <span class="method-post">POST</span>
          <span>/v1/campaigns/:id/decisions</span>
        </div>
        <div class="endpoint-desc">Reviewer signs <code>APPROVED</code> or <code>CHANGES_REQUESTED</code> with mandatory written rationale. Binds hash.</div>
      </div>

      <div class="endpoint-card">
        <div class="endpoint-head">
          <span class="method-patch">PATCH</span>
          <span>/v1/campaigns/:id</span>
        </div>
        <div class="endpoint-desc">Copy-on-write edit. Supersedes current revision, forks new DRAFT, cancels active schedule.</div>
      </div>

      <div class="endpoint-card">
        <div class="endpoint-head">
          <span class="method-post">POST</span>
          <span>/v1/campaigns/:id/schedule</span>
        </div>
        <div class="endpoint-desc">Atomic schedule gate. Requires <code>revisionId</code>, <code>expectedContentHash</code>, and <code>scheduledAt</code>.</div>
      </div>
    </div>

    <div class="error-tax-box">
      <div class="card-title" style="color: #fb7185;"><span class="dot" style="background: #f43f5e;"></span> Deterministic Conflict Taxonomy (409)</div>

      <div class="err-row">
        <div class="err-code">409 REVISION_STALE</div>
        <div class="err-meaning">Requested revision ID does not match <code>campaign.current_revision_id</code>. Another user updated the proposal.</div>
      </div>

      <div class="err-row">
        <div class="err-code">409 APPROVAL_INVALID</div>
        <div class="err-meaning">Current revision is in <code>DRAFT</code> or <code>CHANGES_REQUESTED</code>. Scheduling attempted without reviewer sign-off.</div>
      </div>

      <div class="err-row">
        <div class="err-code">409 CONTENT_HASH_MISMATCH</div>
        <div class="err-meaning">Decision content hash differs from revision SHA-256 hash. Detects silent tampering or corruption.</div>
      </div>

      <div class="err-row">
        <div class="err-code">409 ALREADY_SCHEDULED</div>
        <div class="err-meaning">Active schedule already exists for this campaign container. Prevents double-scheduling races.</div>
      </div>

      <div class="err-row">
        <div class="err-code">403 SELF_REVIEW_PROHIBITED</div>
        <div class="err-meaning">Actor attempted to approve their own proposal. Strict separation of duties violation.</div>
      </div>
    </div>
  </div>

  <div class="footer">
    <div><strong>Deterministic Responses:</strong> Every conflict returns code + current revision snapshot for instant client reconciliation.</div>
    <div>API Protocol Blueprint · Low-Level Design Section 6</div>
  </div>
</body>
</html>
"""

# ==============================================================================
# LLD 5: MASTER LLD BLUEPRINT BOARD
# ==============================================================================
html_lld5 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  {BASE_CSS}
  .master-lld-board {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
    margin-top: 14px;
  }}
  .inv-banner {{
    background: linear-gradient(135deg, #051329 0%, #111d33 100%);
    border: 1.5px solid #0ea5e9;
    border-radius: 8px;
    padding: 10px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 0 20px rgba(14, 165, 233, 0.2);
  }}
  .inv-left {{ font-weight: 850; font-size: 11pt; color: #38bdf8; text-transform: uppercase; }}
  .inv-center {{ font-family: monospace; font-size: 9pt; color: #ffffff; background: rgba(255,255,255,0.08); padding: 4px 12px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.15); }}
  .inv-right {{ font-style: italic; font-size: 9.5pt; color: #cbd5e1; }}
  .board-card {{
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .board-card h3 {{
    font-size: 11pt;
    font-weight: 850;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #38bdf8;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 6px;
  }}
  .board-content {{
    font-size: 8.8pt;
    color: #cbd5e1;
    line-height: 1.4;
  }}
  .board-content strong {{ color: #ffffff; }}
  .item-list {{ list-style: none; padding: 0; }}
  .item-list li {{
    margin-bottom: 8px;
    padding-left: 14px;
    position: relative;
  }}
  .item-list li::before {{
    content: "■";
    position: absolute;
    left: 0;
    font-size: 6pt;
    top: 3px;
    color: #0ea5e9;
  }}
  .pill-tech {{
    display: inline-block;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    padding: 2px 7px;
    border-radius: 3px;
    font-size: 7.5pt;
    margin-right: 4px;
    color: #94a3b8;
  }}
</style>
</head>
<body style="width: 2200px; height: 1020px; padding: 26px 36px;">
  <div class="header">
    <div class="title-group">
      <h1>Campaign Integrity — Master Low-Level Design Blueprint <span class="tag">LLD Specification</span></h1>
      <p>Implementation-Ready Interfaces, Schema DDL, State Transitions & Atomic Gate Engine</p>
    </div>
    <div class="meta-badges">
      <div class="meta-badge highlight">Track: Martech Approval</div>
      <div class="meta-badge">Team: MAL 4</div>
      <div class="meta-badge">1 Nov 2026</div>
    </div>
  </div>

  <div class="inv-banner">
    <div class="inv-left">Atomic Gate Invariant</div>
    <div class="inv-center">active_schedule(c) ⇒ current_rev(c).state = APPROVED ∧ decision.rev_id = current_rev(c).id ∧ decision.content_hash = current_rev(c).content_hash</div>
    <div class="inv-right">“The campaign that gets scheduled is the exact campaign that was approved.”</div>
  </div>

  <div class="master-lld-board">
    <!-- CARD 1: RELATIONAL DATA ENGINE -->
    <div class="board-card">
      <h3>1. Relational Schema & Storage</h3>
      <div class="board-content">
        <ul class="item-list">
          <li><strong>campaigns:</strong> Container row. Holds <code>current_revision_id</code> and acts as row-lock target (<code>SELECT FOR UPDATE</code>).</li>
          <li><strong>revisions:</strong> Append-only immutable tree. Stores objective, audience, channel, budget, state, and SHA-256 content hash.</li>
          <li><strong>decisions:</strong> Reviewer decisions bound strictly to revision ID and content hash.</li>
          <li><strong>schedules:</strong> Holds active or cancelled schedules. Partial unique index guarantees one active schedule per campaign.</li>
          <li><strong>audit_events:</strong> Tamper-evident append-only audit log. Update and delete revoked.</li>
        </ul>
      </div>
    </div>

    <!-- CARD 2: STATE MACHINE & MUTATION -->
    <div class="board-card">
      <h3>2. State Machine & Copy-on-Write</h3>
      <div class="board-content">
        <ul class="item-list">
          <li><strong>5 Core States:</strong> <code>DRAFT</code> ➔ <code>IN_REVIEW</code> ➔ (<code>CHANGES_REQUESTED</code>) ➔ <code>APPROVED</code> ➔ <code>SUPERSEDED</code>.</li>
          <li><strong>Copy-on-Write Mutation:</strong> Editing an approved proposal supersedes revision, revokes prior approval, and cancels active schedule atomically.</li>
          <li><strong>Hash Invalidation:</strong> Any modification to material fields alters SHA-256 hash, causing immediate approval invalidation.</li>
          <li><strong>Deterministic 409 Conflicts:</strong> Stale revision or hash mismatch returns clear error code with current snapshot.</li>
        </ul>
      </div>
    </div>

    <!-- CARD 3: CRITICAL SCHEDULING GATE -->
    <div class="board-card">
      <h3>3. Atomic Scheduling Transaction</h3>
      <div class="board-content">
        <ul class="item-list">
          <li><strong>Exclusive Row-Lock:</strong> <code>SELECT * FROM campaigns FOR UPDATE</code> serializes all concurrent actions.</li>
          <li><strong>Check 1 (Current Rev):</strong> Verifies requested revision equals campaign current revision.</li>
          <li><strong>Check 2 (Approved State):</strong> Verifies revision state is strictly <code>APPROVED</code>.</li>
          <li><strong>Check 3 (Hash Binding):</strong> Verifies decision content hash matches current revision hash.</li>
          <li><strong>Check 4 (Uniqueness):</strong> Asserts no active schedule exists. Inserts schedule + audit atomically.</li>
        </ul>
      </div>
    </div>

    <!-- CARD 4: MODULES & CLEAN ARCHITECTURE -->
    <div class="board-card">
      <h3>4. Modules & Clean Boundaries</h3>
      <div class="board-content">
        <ul class="item-list">
          <li><strong>Domain Core:</strong> Pure TypeScript models, state machine, eligibility logic, and canonical hashing. Imports nothing from Express or SQL.</li>
          <li><strong>Application Layer:</strong> <code>CampaignService</code>, <code>ReviewService</code>, <code>ScheduleService</code>, <code>IdempotencyService</code>.</li>
          <li><strong>Mobile App:</strong> Screens, ViewModels, pure domain helpers, local repositories, SQLite outbox sync.</li>
          <li><strong>Server Persistence:</strong> PostgreSQL repository implementations of domain ports.</li>
        </ul>
      </div>
    </div>

    <!-- CARD 5: API CONTRACTS & IDEMPOTENCY -->
    <div class="board-card">
      <h3>5. API Contracts & Outbox Sync</h3>
      <div class="board-content">
        <ul class="item-list">
          <li><strong>Idempotency Header:</strong> Client passes UUID <code>Idempotency-Key</code> for all state mutating commands.</li>
          <li><strong>Crash Defense:</strong> Mobile writes intent to SQLite outbox before network dispatch. Recovers after process kill.</li>
          <li><strong>Duplicate Suppression:</strong> Server claims key in database. Replayed requests receive exact stored response.</li>
          <li><strong>Audit Attribution:</strong> 100% of state transitions record actor ID, revision, hash, and request ID.</li>
        </ul>
      </div>
    </div>

    <!-- CARD 6: SECURITY & ENFORCEMENT -->
    <div class="board-card">
      <h3>6. Security & Duties Enforcement</h3>
      <div class="board-content">
        <ul class="item-list">
          <li><strong>Separation of Duties:</strong> Service enforces <code>actor_id ≠ campaign.creator_id</code>. Reviewers cannot approve their own campaigns.</li>
          <li><strong>Author Restriction:</strong> Marketer cannot approve any campaign; review role strictly isolated.</li>
          <li><strong>Timeouts Are Failures:</strong> Network disconnects never advance state. Zero optimistic boolean drift.</li>
          <li><strong>Evolvability (ADR-001):</strong> Extension point ready for dual multi-party approvals above budget thresholds.</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="footer" style="margin-top: 18px;">
    <div><strong>Campaign Integrity LLD Master Blueprint:</strong> Architecture-First deliverable for MAL Hackathon 2026.</div>
    <div>Complete Low-Level Architecture Board · Sections 1 through 7</div>
  </div>
</body>
</html>
"""

diagrams = [
    {
        "name": "lld_01_domain_models_schema",
        "html": html_lld1,
        "width": 1600,
        "height": 780
    },
    {
        "name": "lld_02_state_machine_lifecycle",
        "html": html_lld2,
        "width": 1600,
        "height": 780
    },
    {
        "name": "lld_03_atomic_scheduling_transaction",
        "html": html_lld3,
        "width": 1600,
        "height": 780
    },
    {
        "name": "lld_04_api_contracts_outbox",
        "html": html_lld4,
        "width": 1600,
        "height": 780
    },
    {
        "name": "lld_master_architecture_board",
        "html": html_lld5,
        "width": 2200,
        "height": 980
    }
]

print("Starting generation of LLD diagram images...")
generated_files = []

for diag in diagrams:
    html_filename = f"{diag['name']}.html"
    png_filename = f"{diag['name']}.png"
    
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(diag["html"])
    
    html_abs = os.path.abspath(html_filename)
    png_abs = os.path.abspath(png_filename)
    
    cmd = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        f"--screenshot={png_abs}",
        f"--window-size={diag['width']},{diag['height']}",
        html_abs
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(png_abs):
        size = os.path.getsize(png_abs)
        print(f"Generated {png_filename} ({diag['width']}x{diag['height']}) - {size} bytes")
        generated_files.append((png_filename, size))
    else:
        print(f"ERROR: Failed to generate {png_filename}")

print(f"\nCompleted! Generated {len(generated_files)} LLD images successfully in one run.")
