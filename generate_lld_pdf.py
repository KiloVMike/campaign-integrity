import os
import subprocess
import sys

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
cwd = os.path.abspath(".")

# ------------------------------------------------------------------------------
# 1. COMPREHENSIVE MULTI-PAGE LLD PDF
# ------------------------------------------------------------------------------
html_full_lld = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Campaign Integrity — Low-Level Design & Critical Feature Specification</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 14mm 14mm 14mm 14mm;
    @bottom-right {{
      content: counter(page);
    }}
  }}
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #0f172a;
    line-height: 1.4;
    font-size: 9pt;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  .page-break {{
    page-break-after: always;
    break-after: page;
  }}
  .header-band {{
    border-bottom: 2px solid #0f172a;
    padding-bottom: 8px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}
  .title-group h1 {{
    font-size: 20pt;
    font-weight: 900;
    letter-spacing: -0.5px;
    color: #0f172a;
  }}
  .title-group .sub {{
    font-size: 10pt;
    font-weight: 600;
    color: #2563eb;
    margin-top: 2px;
  }}
  .meta-tag {{
    font-size: 8pt;
    color: #475569;
    font-weight: 600;
    text-align: right;
  }}
  .invariant-card {{
    background: #0f172a;
    color: #f8fafc;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 16px;
  }}
  .inv-label {{
    font-size: 8pt;
    font-weight: 800;
    color: #60a5fa;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }}
  .inv-math {{
    font-family: monospace;
    font-size: 8pt;
    background: rgba(255,255,255,0.1);
    padding: 5px 8px;
    border-radius: 4px;
    color: #ffffff;
    display: block;
    margin: 4px 0;
  }}
  .inv-tagline {{
    font-size: 8pt;
    font-style: italic;
    color: #94a3b8;
  }}
  h2 {{
    font-size: 13pt;
    font-weight: 850;
    color: #0f172a;
    border-bottom: 1.5px solid #e2e8f0;
    padding-bottom: 4px;
    margin: 16px 0 10px 0;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  h2 .num {{
    background: #2563eb;
    color: #ffffff;
    font-size: 9pt;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }}
  h3 {{
    font-size: 10pt;
    font-weight: 800;
    color: #1e293b;
    margin: 10px 0 6px 0;
  }}
  p {{
    margin-bottom: 8px;
    color: #334155;
    line-height: 1.45;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 14px 0;
    font-size: 8pt;
  }}
  th {{
    background: #f1f5f9;
    color: #334155;
    font-weight: 750;
    text-align: left;
    padding: 6px 8px;
    border-bottom: 1.5px solid #cbd5e1;
    text-transform: uppercase;
    font-size: 7.5pt;
  }}
  td {{
    padding: 6px 8px;
    border-bottom: 1px solid #e2e8f0;
    color: #1e293b;
    vertical-align: top;
  }}
  .diagram-embed {{
    width: 100%;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    margin: 10px 0 14px 0;
    display: block;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
  }}
  .code-block {{
    background: #0f172a;
    color: #e2e8f0;
    border-radius: 6px;
    padding: 10px 12px;
    font-family: "SFMono-Regular", Consolas, monospace;
    font-size: 7.5pt;
    line-height: 1.35;
    margin: 8px 0 12px 0;
    overflow: hidden;
  }}
  .badge {{
    display: inline-block;
    padding: 1px 5px;
    border-radius: 3px;
    font-weight: 700;
    font-size: 7pt;
    font-family: monospace;
  }}
  .badge-blue {{ background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }}
  .badge-green {{ background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }}
  .badge-amber {{ background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }}
  .badge-red {{ background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }}
  .footer-meta {{
    font-size: 7.5pt;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
    padding-top: 6px;
    margin-top: 20px;
    display: flex;
    justify-content: space-between;
  }}
</style>
</head>
<body>

  <!-- PAGE 1: COVER & SYSTEM INVARIANT -->
  <div>
    <div class="header-band">
      <div class="title-group">
        <h1>CAMPAIGN INTEGRITY</h1>
        <div class="sub">Low-Level Design & Critical Feature Specification</div>
      </div>
      <div class="meta-tag">
        Track: Martech Approval<br/>
        Team: MAL 4 · 1 Nov 2026<br/>
        Architecture Deliverable
      </div>
    </div>

    <div class="invariant-card">
      <div class="inv-label">The Core Architectural Invariant</div>
      <div class="inv-math">active_schedule(c) ⇒ current_rev(c).state = APPROVED ∧ decision.rev_id = current_rev(c).id ∧ decision.content_hash = current_rev(c).content_hash</div>
      <div class="inv-tagline">“The campaign that gets scheduled is the exact campaign that was approved.”</div>
    </div>

    <h2><span class="num">1</span> Executive Architectural Blueprint</h2>
    <p>This document specifies the concrete modules, interfaces, models, states, database schemas, and the atomic scheduling transaction for <strong>Campaign Integrity</strong>. The design eliminates boolean status drift by binding every approval cryptographically and relationally to an immutable revision tree.</p>

    <img class="diagram-embed" src="file:///{cwd}/lld_master_architecture_board.png" alt="LLD Master Blueprint Board">

    <h2><span class="num">2</span> Clean Architecture Module Map</h2>
    <table>
      <thead>
        <tr><th>Layer</th><th>Responsibilities</th><th>May Import</th><th>Forbidden Imports</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Mobile Presentation</strong></td>
          <td>Campaign dashboard, revision comparisons, review drawer, action triggers</td>
          <td>View models, Design System</td>
          <td>SQLite, HTTP client, Server code</td>
        </tr>
        <tr>
          <td><strong>Mobile Application</strong></td>
          <td>Orchestrates reads, enqueues commands, manages local form states</td>
          <td>Domain types, Repository ports</td>
          <td>React Native UI components</td>
        </tr>
        <tr>
          <td><strong>Domain Core</strong></td>
          <td>Pure state machine, eligibility predicates, canonical SHA-256 hash</td>
          <td>Pure TypeScript only</td>
          <td>Express, pg, React Native, SQLite</td>
        </tr>
        <tr>
          <td><strong>Application Services</strong></td>
          <td>Transaction boundaries, command authorization, audit trail emission</td>
          <td>Domain models, Repository ports</td>
          <td>Express request/response objects</td>
        </tr>
        <tr>
          <td><strong>Server Persistence</strong></td>
          <td>SQL queries, row locks (<code>SELECT FOR UPDATE</code>), constraint mapping</td>
          <td>Domain types, pg driver</td>
          <td>HTTP layer, UI layer</td>
        </tr>
      </tbody>
    </table>

    <div class="footer-meta">
      <span>Campaign Integrity · Low-Level Design Specification</span>
      <span>Page 1 of 4</span>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- PAGE 2: RELATIONAL SCHEMA -->
  <div>
    <div class="header-band">
      <div class="title-group">
        <h1>RELATIONAL SCHEMA & DATA MODELS</h1>
        <div class="sub">PostgreSQL System of Record DDL & Integrity Constraints</div>
      </div>
      <div class="meta-tag">LLD Section 5</div>
    </div>

    <img class="diagram-embed" src="file:///{cwd}/lld_01_domain_models_schema.png" alt="Database Schema Architecture">

    <h2><span class="num">3</span> Relational Table Specifications</h2>
    <table>
      <thead>
        <tr><th>Table</th><th>Primary Key</th><th>Key Foreign Keys & Constraints</th><th>Operational Invariant</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><code>campaigns</code></td>
          <td><code>id (CMP-...)</code></td>
          <td><code>current_rev_id ➔ revisions(id)</code></td>
          <td>Root lock target for all concurrent reviews and schedule gates.</td>
        </tr>
        <tr>
          <td><code>revisions</code></td>
          <td><code>id (REV-...)</code></td>
          <td><code>campaign_id ➔ campaigns(id)</code></td>
          <td>Append-only immutable revision tree. Content hash computed over material fields.</td>
        </tr>
        <tr>
          <td><code>decisions</code></td>
          <td><code>id (DEC-...)</code></td>
          <td><code>revision_id ➔ revisions(id)</code></td>
          <td>Bound to exact revision SHA-256 content hash. Cannot exist without revision target.</td>
        </tr>
        <tr>
          <td><code>schedules</code></td>
          <td><code>id (SCH-...)</code></td>
          <td><code>revision_id</code>, <code>decision_id</code></td>
          <td>Partial unique index: exactly ONE active <code>SCHEDULED</code> row per campaign.</td>
        </tr>
        <tr>
          <td><code>audit_events</code></td>
          <td><code>id (AUD-...)</code></td>
          <td><code>correlation_id (UUID)</code></td>
          <td>Tamper-evident append-only log. <code>UPDATE</code> and <code>DELETE</code> revoked at database level.</td>
        </tr>
        <tr>
          <td><code>idempotency_keys</code></td>
          <td><code>key (UUID)</code></td>
          <td><code>request_hash (SHA-256)</code></td>
          <td>Deduplication engine. Replays cached response body for network retries.</td>
        </tr>
      </tbody>
    </table>

    <h2><span class="num">4</span> Canonical Content Hashing (SHA-256)</h2>
    <p>Every proposal revision computes a canonical SHA-256 hash across material fields to guarantee bit-level integrity:</p>
    <div class="code-block">
function computeCanonicalHash(rev: ProposalContent): string {{
  const payload = JSON.stringify({{
    objective: rev.objective.trim(),
    audience: rev.audience.trim(),
    channel: rev.channel,
    budgetPaise: rev.budgetPaise.toString()
  }});
  return crypto.createHash("sha256").update(payload, "utf8").digest("hex");
}}
    </div>

    <div class="footer-meta">
      <span>Campaign Integrity · Low-Level Design Specification</span>
      <span>Page 2 of 4</span>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- PAGE 3: STATE MACHINE & ATOMIC SCHEDULING GATE -->
  <div>
    <div class="header-band">
      <div class="title-group">
        <h1>REVISION STATE MACHINE & ATOMIC GATE</h1>
        <div class="sub">Deterministic Transitions & The Critical Feature Transaction</div>
      </div>
      <div class="meta-tag">LLD Section 3 & 4</div>
    </div>

    <img class="diagram-embed" src="file:///{cwd}/lld_02_state_machine_lifecycle.png" alt="State Machine Lifecycle">

    <h2><span class="num">5</span> Critical Feature: Atomic Scheduling Transaction</h2>
    <p>Scheduling is evaluated within a single PostgreSQL ACID transaction under exclusive row-lock (<code>SELECT ... FOR UPDATE</code>). Zero race windows exist between concurrent edits and reviewer actions:</p>

    <img class="diagram-embed" src="file:///{cwd}/lld_03_atomic_scheduling_transaction.png" alt="Atomic Scheduling Transaction Walkthrough">

    <h2><span class="num">6</span> Transaction Implementation (TypeScript)</h2>
    <div class="code-block">
export class ScheduleService {{
  async schedule(cmd: ScheduleCommand, ctx: RequestContext): Promise&lt;ScheduleResult&gt; {{
    return this.pg.transaction(async (tx) => {{
      // 1. Acquire exclusive lock on campaign root
      const campaign = await tx.query("SELECT * FROM campaigns WHERE id = $1 FOR UPDATE", [cmd.campaignId]);
      
      // Check 1: Current revision check
      if (cmd.revisionId !== campaign.current_revision_id) {{
        throw new ConflictError("REVISION_STALE", {{ current: campaign.current_revision_id }});
      }}
      
      // Check 2: Approved state check
      const rev = await this.revRepo.getById(tx, cmd.revisionId);
      if (rev.state !== "APPROVED") {{
        throw new ConflictError("APPROVAL_INVALID", {{ state: rev.state }});
      }}
      
      // Check 3: Cryptographic content hash equality
      const dec = await this.decRepo.getActiveDecision(tx, rev.id);
      if (dec.contentHash !== rev.contentHash) {{
        throw new ConflictError("CONTENT_HASH_MISMATCH");
      }}
      
      // Check 4: Schedule uniqueness check
      if (await this.schedRepo.hasActiveSchedule(tx, campaign.id)) {{
        throw new ConflictError("ALREADY_SCHEDULED");
      }}
      
      // Commit schedule and audit event atomically
      const schedule = await this.schedRepo.create(tx, {{ campaignId: campaign.id, revId: rev.id, decId: dec.id }});
      await this.auditRepo.emit(tx, {{ type: "CAMPAIGN_SCHEDULED", campaignId: campaign.id, revId: rev.id, actorId: ctx.actorId }});
      return schedule;
    }});
  }}
}}
    </div>

    <div class="footer-meta">
      <span>Campaign Integrity · Low-Level Design Specification</span>
      <span>Page 3 of 4</span>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- PAGE 4: API CONTRACTS, OUTBOX & DEFENSIBILITY -->
  <div>
    <div class="header-band">
      <div class="title-group">
        <h1>API PROTOCOLS & RUNTIME RESILIENCE</h1>
        <div class="sub">Idempotent Commands, Conflict Envelopes & Offline Outbox</div>
      </div>
      <div class="meta-tag">LLD Section 6 & 7</div>
    </div>

    <img class="diagram-embed" src="file:///{cwd}/lld_04_api_contracts_outbox.png" alt="API Contracts and Error Taxonomy">

    <h2><span class="num">7</span> RESTful API Command Specifications</h2>
    <table>
      <thead>
        <tr><th>Endpoint</th><th>Method</th><th>Idempotency</th><th>Key Validation</th><th>Domain Effect</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><code>/v1/campaigns</code></td>
          <td><span class="badge badge-blue">POST</span></td>
          <td>Required</td>
          <td>Schema & fields</td>
          <td>Creates campaign + Revision 1 (DRAFT)</td>
        </tr>
        <tr>
          <td><code>/v1/campaigns/:id/submit</code></td>
          <td><span class="badge badge-blue">POST</span></td>
          <td>Required</td>
          <td>Author role</td>
          <td>Locks Rev 1; state moves to IN_REVIEW</td>
        </tr>
        <tr>
          <td><code>/v1/campaigns/:id/decisions</code></td>
          <td><span class="badge badge-blue">POST</span></td>
          <td>Required</td>
          <td><code>reviewer ≠ author</code></td>
          <td>Inserts decision bound to SHA-256 hash; state ➔ APPROVED</td>
        </tr>
        <tr>
          <td><code>/v1/campaigns/:id</code></td>
          <td><span class="badge badge-amber">PATCH</span></td>
          <td>Required</td>
          <td>Author role</td>
          <td>Copy-on-write fork: Rev 2 DRAFT created; cancels active schedule!</td>
        </tr>
        <tr>
          <td><code>/v1/campaigns/:id/schedule</code></td>
          <td><span class="badge badge-blue">POST</span></td>
          <td>Required</td>
          <td>Row-lock gate</td>
          <td>Evaluates 4 checks; inserts schedule + audit row atomically</td>
        </tr>
      </tbody>
    </table>

    <h2><span class="num">8</span> Defensibility Matrix & Quality Guarantees</h2>
    <table>
      <thead>
        <tr><th>Quality Attribute</th><th>Concrete Failure Scenario</th><th>Architectural Defense Mechanism</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Integrity</strong></td>
          <td>Marketer alters budget post-approval and attempts schedule.</td>
          <td>Copy-on-write supersedes revision; hash mismatch rejects schedule via atomic gate.</td>
        </tr>
        <tr>
          <td><strong>Recoverability</strong></td>
          <td>App crashes or loses connectivity mid-command.</td>
          <td>Client SQLite outbox retains intent; background sync retries with identical UUID key.</td>
        </tr>
        <tr>
          <td><strong>Concurrency</strong></td>
          <td>Reviewer approves while marketer submits simultaneous edit.</td>
          <td>PostgreSQL row lock (<code>SELECT FOR UPDATE</code>) on campaign serializes execution.</td>
        </tr>
        <tr>
          <td><strong>Auditability</strong></td>
          <td>Auditor inspects historical decision for regulatory review.</td>
          <td>Append-only <code>audit_events</code> logs actor, timestamp, revision ID, hash, and request ID.</td>
        </tr>
      </tbody>
    </table>

    <div class="footer-meta">
      <span>Campaign Integrity · Low-Level Design Specification</span>
      <span>Page 4 of 4 (End of Document)</span>
    </div>
  </div>

</body>
</html>
"""

# Write HTML file
with open("low_level_design.html", "w", encoding="utf-8") as f:
    f.write(html_full_lld)

html_abs = os.path.abspath("low_level_design.html")
pdf_output = os.path.abspath("Campaign-Integrity-Low-Level-Design.pdf")

cmd_pdf = [
    chrome_path,
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--run-all-compositor-stages-before-draw",
    f"--print-to-pdf={pdf_output}",
    html_abs
]

print("Rendering Campaign-Integrity-Low-Level-Design.pdf...")
subprocess.run(cmd_pdf, capture_output=True, text=True)

if os.path.exists(pdf_output):
    size = os.path.getsize(pdf_output)
    with open(pdf_output, "rb") as f:
        data = f.read()
    page_count = data.count(b"/Type /Page") - data.count(b"/Type /Pages")
    print(f"Generated {pdf_output} ({size} bytes, {page_count} pages)")
else:
    print("ERROR: Failed to generate LLD PDF")

# ------------------------------------------------------------------------------
# 2. ALSO GENERATE 1-PAGE LLD EXECUTIVE SUMMARY PDF
# ------------------------------------------------------------------------------
html_1page_lld = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Campaign Integrity — Low-Level Design One-Page Brief</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 0;
  }}
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 210mm;
    height: 297mm;
    background: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #0f172a;
    line-height: 1.28;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  .page {{
    width: 210mm;
    height: 297mm;
    padding: 7mm 9.5mm 6mm 9.5mm;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .header {{
    border-bottom: 2px solid #0f172a;
    padding-bottom: 4px;
    margin-bottom: 5px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}
  .title-group h1 {{ font-size: 19pt; font-weight: 900; letter-spacing: -0.5px; color: #0f172a; }}
  .title-group .sub {{ font-size: 9pt; font-weight: 650; color: #0284c7; margin-top: 1px; }}
  .meta-tag {{ font-size: 7.2pt; color: #334155; font-weight: 600; text-align: right; }}
  .inv-box {{
    background: linear-gradient(135deg, #07172f 0%, #0f172a 100%);
    color: #ffffff;
    border-radius: 5px;
    padding: 5px 10px;
    margin-bottom: 6px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }}
  .inv-row {{ display: flex; justify-content: space-between; font-size: 7.2pt; }}
  .inv-code {{
    font-family: monospace;
    font-size: 6.8pt;
    background: rgba(255,255,255,0.08);
    padding: 3px 6px;
    border-radius: 3px;
    border: 1px solid rgba(255,255,255,0.18);
    text-align: center;
    color: #ffffff;
  }}
  .grid-2col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 7px;
    flex-grow: 1;
    margin-bottom: 4px;
  }}
  .card {{
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 6px 8px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .card-head {{
    font-size: 8.2pt;
    font-weight: 850;
    text-transform: uppercase;
    color: #0f172a;
    border-bottom: 1.5px solid #f1f5f9;
    padding-bottom: 2.5px;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 5px;
  }}
  .card-num {{
    background: #0284c7;
    color: #ffffff;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    font-size: 6.8pt;
    font-weight: 850;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }}
  .tbl-mini {{
    width: 100%;
    border-collapse: collapse;
    font-size: 6.8pt;
  }}
  .tbl-mini th {{
    background: #f8fafc;
    color: #475569;
    font-weight: 750;
    padding: 2.5px 4px;
    border-bottom: 1px solid #cbd5e1;
    text-align: left;
  }}
  .tbl-mini td {{
    padding: 3px 4px;
    border-bottom: 1px solid #f1f5f9;
    color: #1e293b;
    vertical-align: top;
  }}
  .code-snip {{
    background: #0f172a;
    color: #e2e8f0;
    font-family: monospace;
    font-size: 6.5pt;
    padding: 5px 6px;
    border-radius: 4px;
    line-height: 1.25;
  }}
  .footer {{
    border-top: 1.5px solid #cbd5e1;
    padding-top: 3.5px;
    display: flex;
    justify-content: space-between;
    font-size: 7.2pt;
    color: #64748b;
  }}
</style>
</head>
<body>
<div class="page">
  <div>
    <div class="header">
      <div class="title-group">
        <h1>CAMPAIGN INTEGRITY — LLD BRIEF</h1>
        <div class="sub">Low-Level Design & Critical Feature Architecture Specification</div>
      </div>
      <div class="meta-tag">
        Track: Martech · Team: MAL 4<br/>
        Deliverable: One-Page LLD Brief
      </div>
    </div>

    <div class="inv-box">
      <div class="inv-row">
        <span style="font-weight: 850; color: #38bdf8;">THE CRITICAL FEATURE INVARIANT</span>
        <span style="font-style: italic; color: #cbd5e1;">“The campaign that gets scheduled is the exact campaign that was approved.”</span>
      </div>
      <div class="inv-code">
        active_schedule(c) ⇒ current_rev(c).state = APPROVED ∧ decision.rev_id = current_rev(c).id ∧ decision.content_hash = current_rev(c).content_hash
      </div>
    </div>
  </div>

  <div class="grid-2col">
    <!-- LEFT COLUMN -->
    <div style="display: flex; flex-direction: column; gap: 6px; justify-content: space-between;">
      
      <!-- 1. RELATIONAL DDL -->
      <div class="card">
        <div class="card-head"><span class="card-num">1</span> Relational Schema & Indices</div>
        <table class="tbl-mini">
          <thead>
            <tr><th>Table</th><th>Keys & Constraints</th><th>Invariant Target</th></tr>
          </thead>
          <tbody>
            <tr>
              <td><code>campaigns</code></td>
              <td><code>id (PK), current_rev_id (FK)</code></td>
              <td>Lock root: <code>SELECT FOR UPDATE</code></td>
            </tr>
            <tr>
              <td><code>revisions</code></td>
              <td><code>id (PK), campaign_id, content_hash</code></td>
              <td>Immutable copy-on-write version tree</td>
            </tr>
            <tr>
              <td><code>decisions</code></td>
              <td><code>id (PK), revision_id, hash</code></td>
              <td>Cryptographically bound reviewer approval</td>
            </tr>
            <tr>
              <td><code>schedules</code></td>
              <td><code>id (PK), rev_id, dec_id</code></td>
              <td>Partial unique index: 1 active schedule/cmp</td>
            </tr>
            <tr>
              <td><code>audit_events</code></td>
              <td><code>id (PK), actor_id, rev_id, correlation_id</code></td>
              <td>Insert-only; UPDATE/DELETE revoked</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 2. REVISION STATE MACHINE -->
      <div class="card">
        <div class="card-head"><span class="card-num">2</span> Revision State Machine & Mutations</div>
        <table class="tbl-mini">
          <thead>
            <tr><th>Transition</th><th>Trigger Action</th><th>Enforced Guard</th></tr>
          </thead>
          <tbody>
            <tr>
              <td><code>DRAFT ➔ IN_REVIEW</code></td>
              <td>Submit for review</td>
              <td>Author only; complete fields</td>
            </tr>
            <tr>
              <td><code>IN_REVIEW ➔ APPROVED</code></td>
              <td>Reviewer approves</td>
              <td><code>reviewer ≠ author ∧ hash_match</code></td>
            </tr>
            <tr>
              <td><code>IN_REVIEW ➔ CHANGES_REQ</code></td>
              <td>Request changes</td>
              <td>Mandatory written rationale note</td>
            </tr>
            <tr>
              <td><code>APPROVED ➔ SCHEDULED</code></td>
              <td>Schedule campaign</td>
              <td>Single atomic gate checks pass</td>
            </tr>
            <tr>
              <td><code>APPROVED ➔ SUPERSEDED</code></td>
              <td>Post-approval edit</td>
              <td>Copy-on-write fork; cancels schedule!</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 3. CLEAN ARCHITECTURE BOUNDARIES -->
      <div class="card">
        <div class="card-head"><span class="card-num">3</span> Clean Architecture Layer Boundaries</div>
        <div style="font-size: 6.8pt; color: #334155; line-height: 1.25;">
          <strong>Mobile Client:</strong> Presentation ➔ Use Cases ➔ Domain Helpers ➔ Repositories ➔ SQLite Outbox.<br/>
          <strong>API Monolith:</strong> HTTP Transport ➔ Application Services (Tx Boundary) ➔ Domain Core ➔ Persistence Repositories ➔ PostgreSQL.<br/>
          <strong>Dependency Rule:</strong> Domain core imports NOTHING from Express, SQL, or React Native.
        </div>
      </div>

    </div>

    <!-- RIGHT COLUMN -->
    <div style="display: flex; flex-direction: column; gap: 6px; justify-content: space-between;">
      
      <!-- 4. ATOMIC SCHEDULING GATE -->
      <div class="card">
        <div class="card-head"><span class="card-num">4</span> The Atomic Scheduling Gate (Tx)</div>
        <div class="code-snip">
// ScheduleService.execute() inside PostgreSQL transaction:
const c = await tx.query("SELECT * FROM campaigns WHERE id=$1 FOR UPDATE", [id]);
if (req.revId !== c.current_revision_id) throw new ConflictError("REVISION_STALE");
const rev = await getRevision(tx, req.revId);
if (rev.state !== "APPROVED") throw new ConflictError("APPROVAL_INVALID");
const dec = await getActiveDecision(tx, rev.id);
if (dec.content_hash !== rev.content_hash) throw new ConflictError("HASH_MISMATCH");
if (await hasActiveSchedule(tx, c.id)) throw new ConflictError("ALREADY_SCHEDULED");
await insertSchedule(tx, ...);
await insertAudit(tx, "CAMPAIGN_SCHEDULED", ...);
        </div>
      </div>

      <!-- 5. REST API CONTRACTS & 409 ERRORS -->
      <div class="card">
        <div class="card-head"><span class="card-num">5</span> API Endpoints & 409 Conflict Envelopes</div>
        <table class="tbl-mini">
          <thead>
            <tr><th>HTTP Command</th><th>Key Payload / Header</th><th>Deterministic Conflict Response</th></tr>
          </thead>
          <tbody>
            <tr>
              <td><code>POST /campaigns</code></td>
              <td><code>Idempotency-Key</code>, title, budget</td>
              <td>400 Validation Error</td>
            </tr>
            <tr>
              <td><code>POST /submit</code></td>
              <td><code>Idempotency-Key</code></td>
              <td>409 REVISION_NOT_DRAFT</td>
            </tr>
            <tr>
              <td><code>POST /decisions</code></td>
              <td><code>APPROVED | CHANGES_REQ</code></td>
              <td>403 SELF_REVIEW_PROHIBITED</td>
            </tr>
            <tr>
              <td><code>PATCH /campaigns/:id</code></td>
              <td>New budget, audience, objective</td>
              <td>Copy-on-write fork (auto-cancel schedule)</td>
            </tr>
            <tr>
              <td><code>POST /schedule</code></td>
              <td><code>revisionId, expectedHash</code></td>
              <td>409 REVISION_STALE | HASH_MISMATCH</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 6. RESILIENCE & OUTBOX SYNC -->
      <div class="card">
        <div class="card-head"><span class="card-num">6</span> Resilience & Defensibility Tactics</div>
        <div style="font-size: 6.8pt; color: #334155; line-height: 1.25;">
          <strong>SQLite Command Outbox:</strong> Persists user intent locally prior to dispatch; sync engine recovers seamlessly after app kill.<br/>
          <strong>Exactly-Once Idempotency:</strong> Client UUID keys guarantee retried requests return cached responses with zero duplicate state mutations.<br/>
          <strong>Derived Not Stored:</strong> Approval is computed dynamically. Eliminates mutable boolean drift entirely.
        </div>
      </div>

    </div>
  </div>

  <div class="footer">
    <span>MAL 4 · Hackathon Architecture Deliverable · Track: Martech</span>
    <span>“The campaign that gets scheduled is the campaign that was approved.”</span>
    <span style="font-weight: 700; color: #0f172a;">A4 Portrait · Exactly 1 Page</span>
  </div>
</div>
</body>
</html>
"""

with open("low_level_design_one_page.html", "w", encoding="utf-8") as f:
    f.write(html_1page_lld)

html_1p_abs = os.path.abspath("low_level_design_one_page.html")
pdf_1p_output = os.path.abspath("Campaign-Integrity-LLD-One-Page.pdf")

cmd_1p_pdf = [
    chrome_path,
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--run-all-compositor-stages-before-draw",
    f"--print-to-pdf={pdf_1p_output}",
    html_1p_abs
]

print("Rendering Campaign-Integrity-LLD-One-Page.pdf...")
subprocess.run(cmd_1p_pdf, capture_output=True, text=True)

if os.path.exists(pdf_1p_output):
    size = os.path.getsize(pdf_1p_output)
    with open(pdf_1p_output, "rb") as f:
        data = f.read()
    page_count = data.count(b"/Type /Page") - data.count(b"/Type /Pages")
    print(f"Generated {pdf_1p_output} ({size} bytes, {page_count} pages)")
