---
name: watch-gate
description: Design and audit what happens after release — monitoring that would actually catch a break, watchdogs that verify independently and never self-repair, heartbeats whose silence is the alarm, freshness audits for artifacts that rot, and honest cost/quality telemetry measured from real transcripts rather than self-report. Use when adding monitoring, alerting, a scheduled job, or telemetry; when asking whether a failure would be noticed; or when deciding whether an automated check or review step is earning its cost.
---

# watch-gate

The question this gate answers is narrow and uncomfortable: **if this broke right
now, how would we find out, and how long would it take?** If the honest answer is
"a user would tell us," that is the finding.

Canon: `../principles/SKILL.md` — principle 1 (verified beats assumed) and
principle 5 (reversibility decides who acts).

Applies whether the thing being watched is a deployed service, a scheduled job, or
an automated check in your own workflow.

---

## Would we find out?

For each way the change can fail, name the detection path and its latency:

| Failure | Detected by | Latency | Or: nobody notices |
|---|---|---|---|

Any row ending in "nobody notices" is either accepted deliberately and in writing,
or it is the work this gate just found.

Distinguish three things that get conflated:
- **Errors** — it threw. Usually already visible.
- **Silent wrong answers** — it succeeded and was wrong. Needs a correctness check,
  not an error monitor. This is the expensive category and the one that is almost
  always missing.
- **Absence** — it never ran at all. Needs a heartbeat; no error will ever fire.

## Watchdog design

A watchdog verifies that an automated action actually did what it claimed. Six
properties, and it is untrustworthy without all six:

1. **Independent.** Correctness is derived from live ground truth, never from the
   action's own report. A watchdog reading the same log the actor wrote verifies
   nothing.
2. **Verification only.** It surfaces problems with a diagnosis. **It never fixes
   what it finds** — a self-repairing watchdog is an unverified actor wearing a
   monitor's name, and now nothing checks *it*.
3. **Deterministic where possible.** The strongest watchdog is a plain script with
   no model in it, comparing recorded actions against live state. No nondeterminism,
   no injection surface.
4. **Two severities.** Correctness failures alarm immediately. Drift is reported for
   eventual attention. One severity level means everything gets treated like the
   least urgent thing on it.
5. **Silent on success.** No output when the check is clean. A job that says
   "nothing to report" every run trains everyone to ignore it, and then it is
   decorative.
6. **Extensible by construction.** Every new automated action gets a matching
   check, in the same change. "We'll add the watchdog after" means there is no
   watchdog.

## Scheduled job design

Watchdog properties 3 and 5 apply here too — and silent-on-no-op is the most
violated rule on this page.

- **Incremental, not full rescan.** Track what has been processed; handle only what
  is new. Full rescans get slower until they get disabled.
- **Idempotent.** Running twice must equal running once, so a retry is always safe.
- **One heartbeat.** Exactly one job reports unconditionally, on a schedule. Its
  **absence** is the alarm — that is the only way to detect a monitoring system
  that itself died.
- **Concurrency and orphans.** A lock so two runs cannot collide; detection for work
  that was picked up and abandoned mid-flight.
- **Failures surface.** An error in the job must reach a human. A job whose failures
  are only in its own log is not monitored.
- **A scheduled job can send a prompt but cannot receive an answer.** Never design a
  flow where an unattended job waits for approval. The pattern that works:
  **notify from the job, act on the reply** — the notification is one action, and a
  human's response later triggers a separate, fresh action.

## State and artifacts that rot

- **Never treat stored state as authoritative.** Re-derive from live truth before
  acting on it. Records are for audit; ground truth is for decisions.
- **Three axes of verification.** Stored state can be wrong in three independent
  ways, and checking one does not cover the others:
  1. **Action correctness** — did the thing actually happen, per the live surface?
  2. **Ledger honesty** — does the record match live system state?
  3. **Artifact freshness** — does the document still describe the current code?
- **Freshness audit.** For any document, config, or generated artifact that cites
  code — paths, symbols, function names, line references — a scheduled read-only
  check re-reads those citations against current `HEAD` and flags what no longer
  resolves. Documentation rot is invisible until someone trusts it.
- **Reconcile pattern.** A scheduled job diffing your records against ground truth.
  Unambiguous gaps are recorded automatically; anything requiring judgment is
  surfaced, never guessed.
- **State handoff**, when work must survive a process ending: durable rather than
  in-context; discoverable at a known location; **never authoritative**;
  append-only for records or reconciled for queues; and self-describing, meaning
  readable by someone without the private context that created it. Append-only
  markdown at a known path is a fine default; a structured store earns its
  complexity only at real volume or with concurrent writers.
- **Discovery over delivery.** Maintain a pull-based index of anything needing
  attention, as the primary surface. Push notifications are optional and should
  fire on findings only. And separate the **disposable audit trail** (run logs, scan
  summaries) from **actionable output** (drafts, findings, queued decisions) — the
  latter has a lifecycle and must be marked done and archived; the former can be
  dropped.

## Telemetry that tells the truth

Measuring whether an automated check earns its cost, or whether a change helped:

- **Never let self-reported metrics drive a decision.** A component's own report of
  its cost or success is a cross-check at best. Measure externally.
  `scripts/agent-roi.py` in this plugin does this for agent token cost: it parses
  session transcripts directly for real per-invocation usage, rather than trusting
  anything a component says about itself.
- **Score blind.** Whoever judges quality must not know which variant produced the
  output, which trial it was, or what result is hoped for. Identical task wording
  across arms; no labels in prompts.
- **Discount what is cheap.** When comparing cost, account for the parts that are
  nearly free — cached reads, warm paths — or you will optimize the wrong number.
- **Variance before conclusions.** If the spread across runs approaches the size of
  the difference you are measuring, you have measured nothing. Add runs or report
  the result as inconclusive.
- **Retire what does not pay.** A check whose quality contribution does not exceed
  its own run-to-run noise is costing time and attention for nothing. Deleting it is
  a real improvement.

## Verdict

```
Detection:    <failure → detector → latency, one line each>
Not detected: <failure modes with no detector — the work this gate found>
Silent-wrong: <how a wrong-but-successful result is caught | NOT CAUGHT>
Absence:      <heartbeat present? what its silence means>
Findings:     <watchdog / job / freshness / telemetry violations>
Accepted blind spots: <listed, with the decision to accept them>
```
