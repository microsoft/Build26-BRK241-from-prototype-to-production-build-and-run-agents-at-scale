# Field Operations Agent — Validation Questions

A scripted set of questions to confirm the deployed agent is working and that
every tool returns **grounded** answers. Each question lists the **expected
answer** and the **source** it must come from, so you can tell a real tool call
from a hallucination.

**Where to ask:** the Foundry **agent playground** (portal) for the hosted
agent, or locally with:

```bash
azd ai agent invoke --local "<question>"
```

**How to tell it passed:** the answer must contain the **specific number, date,
or name** shown below. For `supplier_docs` answers, the agent should also cite a
**filename** (e.g. `cascade-fiber-safety-attestation.md`). Vague answers with no
specifics mean the tool was **not** invoked.

---

## 0. One-line smoke test (start here)

| Ask | Expect | Source |
| --- | --- | --- |
| *What is Cascade Fiber's safety EMR and when was their last safety audit?* | EMR **0.78**, audit **2026-03-12 (Pass, no findings)** | `supplier_docs` → `cascade-fiber-safety-attestation.md` |

If this returns the exact numbers with a filename citation, the full Foundry IQ
chain (corpus → index → knowledge base → toolbox → `TOOLBOX_ENDPOINT`) is live.

---

## 1. `supplier_docs` — Foundry IQ knowledge base (the newly-wired tool)

Corpus = 12 supplier documents for **two** suppliers. These questions are
answerable **only** from that knowledge content.

### Cascade Fiber Services, LLC (`MSA-2026-CF-0417`, Rev D)

| # | Question | Expected answer | Source doc |
| --- | --- | --- | --- |
| 1 | What is Cascade Fiber's EMR rating? | **0.78** | safety-attestation |
| 2 | When was Cascade Fiber's last safety audit and what was the result? | **2026-03-12** — Pass, no findings | safety-attestation |
| 3 | What is Cascade Fiber's after-hours labor rate? | **$235.00/hour** (code LBR-AH) | rate-card |
| 4 | What does Cascade Fiber charge for a P1 emergency dispatch? | **$310.00/hour** (LBR-P1, ≤2h response) | rate-card |
| 5 | What's the per-strand fusion splice rate for Cascade Fiber? | **$38.50 per strand** (SPL-FUS) | rate-card |
| 6 | What is Cascade Fiber's P1 on-site SLA and the credit if missed? | On-site **2 hours**, ack **15 min**, **15%** credit | SLA |
| 7 | What is Cascade Fiber's monthly availability target and max loss budget? | **99.9%**, **2.5 dB** | SLA |
| 8 | Who is Cascade Fiber's insurance carrier and what's the policy number? | **Northwest Mutual Surety**, **COI-CF-99431** | certificate-of-insurance |
| 9 | What are Cascade Fiber's liability limits and COI expiry? | GL **$2,000,000** / Prof **$1,000,000**, expires **2026-12-31** | certificate-of-insurance |
| 10 | What's the after-hours dispatch number for Cascade Fiber? | **+1-509-555-0142** | MSA |
| 11 | Which site, connector, and spare locker does Cascade Fiber cover? | **Quincy North B-side**, **LC/UPC Duplex**, locker **B-3** (MTP-24 trunks) | dispatch-quick-reference |
| 12 | What is the term of the Cascade Fiber master agreement? | **2026-01-01 to 2027-12-31** | MSA |

### Pacific OptoLink Networks, Inc. (`MSA-2026-PO-0291`, Rev B)

| # | Question | Expected answer | Source doc |
| --- | --- | --- | --- |
| 13 | What is Pacific OptoLink's EMR rating? | **0.69** | safety-attestation |
| 14 | When was Pacific OptoLink's last safety audit and were there findings? | **2026-04-02** — Pass, one advisory (**laser signage refresh**) | safety-attestation |
| 15 | What is Pacific OptoLink's P1 emergency dispatch rate? | **$345.00/hour** (LBR-P1, ≤90m response) | rate-card |
| 16 | What does Pacific OptoLink charge for ROADM degree provisioning? | **$480.00 per degree** (ROADM-PROV) | rate-card |
| 17 | What is Pacific OptoLink's P1 SLA (ack, on-site, credit)? | Ack **10 min**, on-site **1.5 h**, **20%** credit | SLA |
| 18 | What's Pacific OptoLink's availability target and max loss budget? | **99.95%**, **2.2 dB** | SLA |
| 19 | Who is Pacific OptoLink's insurance carrier and policy number? | **Cascadia Casualty Group**, **COI-PO-77204** | certificate-of-insurance |
| 20 | What are Pacific OptoLink's liability limits and COI expiry? | GL **$3,000,000** / Prof **$2,000,000**, expires **2027-01-31** | certificate-of-insurance |
| 21 | What site and connector type does Pacific OptoLink cover, and any mating warning? | **Wenatchee East D-side**, **LC/APC Duplex** (MPO-16) — **do NOT mate APC with UPC** | dispatch-quick-reference |
| 22 | What's Pacific OptoLink's after-hours dispatch number? | **+1-206-555-0188** | MSA |

### Cross-document reasoning (best demo — pulls multiple docs)

| # | Question | Expected answer |
| --- | --- | --- |
| 23 | Compare Cascade Fiber and Pacific OptoLink on safety EMR — which is safer to dispatch? | Pacific OptoLink (**0.69**) is lower/safer than Cascade Fiber (**0.78**) |
| 24 | Which supplier has the faster P1 on-site response? | Pacific OptoLink (**1.5 h**) beats Cascade Fiber (**2 h**) |
| 25 | Which supplier carries higher insurance limits? | Pacific OptoLink (**$3M/$2M**) vs Cascade Fiber (**$2M/$1M**) |
| 26 | Both COIs — which expires first and when? | **Cascade Fiber**, **2026-12-31** (Pacific expires 2027-01-31) |
| 27 | For an urgent after-hours P1 at the lowest cost, which supplier and rate? | **Cascade Fiber**, **$310/hour** (vs Pacific $345/hour) |

---

## 2. Local function tools (bundled sample data — always work)

These run from deterministic mock data in `worker_agent.py`, so they pass with
no extra wiring.

| # | Question | Expected answer | Tool |
| --- | --- | --- | --- |
| 28 | What's the fiber spec for the Quincy North B-side? | **OS2 Single-Mode**, **LC/UPC Duplex**, **48** panels, loss budget **2.5 dB** | `search_site_specs` |
| 29 | When was the Quincy North B-side last audited? | **2026-04-15**; 400G-capable since Q1 2026, trunks tested to IL < 0.15 dB | `search_site_specs` |
| 30 | Any P1 work orders assigned to me? | **WO-20260524-001** — replace failed QSFP-DD in **Rack B-14** | `search_work_iq` |
| 31 | What parts do I need for the P1 transceiver job? | **QSFP-DD 400G SR8**, IBC cleaner, dust caps | `search_work_iq` |
| 32 | What's the procedure to replace a QSFP-DD transceiver? | 10 steps, ~**15 min**, ESD strap, **≤5N** insertion force, BER test 60s | `get_repair_procedure` |
| 33 | How do I do a fiber fusion splice and what loss should I expect? | ~**20 min**, target estimated loss **< 0.02 dB**, OTDR both ends | `get_repair_procedure` |

---

## 3. Real integrations (optional — only if configured)

These call live services and are **left unset by default** (the agent degrades
gracefully). Validate them only after wiring the env vars in
[SETUP-INTEGRATIONS.md](SETUP-INTEGRATIONS.md).

| # | Question | Expected behavior | Requires |
| --- | --- | --- | --- |
| 34 | What's the incident trend for Quincy North over the last 30 days? | Live telemetry answer from OneLake — **or** a clear "not configured" message | `FABRIC_*` (Fabric data agent) |
| 35 | A user asks for a site's "last service date" — how should you handle it? | Agent clarifies **internal vs third-party** visits before answering | Procedural memory (seed fallback works in `hybrid` mode) |

---

## Pass / fail cheat-sheet

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `supplier_docs` answers are vague / no filename cited | `TOOLBOX_ENDPOINT` not injected, or tool not invoked | Confirm `agent.yaml` has `TOOLBOX_ENDPOINT: ${TOOLBOX_ENDPOINT}` and redeploy (see SETUP-INTEGRATIONS.md Step 7) |
| Numbers are wrong / made up | Model answered without the tool | Re-ask more directly ("look up …"); check the toolbox `tools/list` exposes `supplier_docs` |
| Q34 returns "not configured" | Fabric env vars unset | Optional — wire `FABRIC_*` per SETUP-INTEGRATIONS.md |
| Everything vague, even local tools | Agent/model deployment issue | Check the agent version is running and `MODEL_DEPLOYMENT_NAME` resolves |
