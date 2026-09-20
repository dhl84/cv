# David H. Lee — finance systems, regulated payments, and the tooling to run them

CIMA-qualified (ACMA, CGMA) finance lead with a Computer Science degree (UCL). Twelve years across regulated fintech (Revolut, Apron Payments, Ledger Rocket), private equity (Bregal) and consulting (KPMG, CAPCO). I build the control as well as the number: SQL, Python, and AI coding agents applied to reconciliations, close, forecasting and regulatory reporting.

This repository holds two things I am willing to show in public.

## 1. CASS 15 first-audit readiness checklist

`safeguarding/cass15-first-audit-readiness-checklist.pdf`

Since 7 May 2026 every UK authorised payment institution and e-money institution has to reconcile safeguarded funds daily, file a monthly safeguarding return, and pass an annual safeguarding audit that reports to the FCA (PS25/12, CASS 15). The first audit period is running now, and the FRC's guidance is explicit that a control reconstructed after the fact does not count.

The checklist is the set of questions an auditor will effectively ask, phrased so that a CFO or the designated safeguarding individual can answer them without a compliance adviser in the room. It comes from having built and handed over exactly this control at an FCA-authorised EMI, and from leading the finance side of the accounting-rules-engine programme at Revolut that resolved a qualified audit and specified the feeds for CASS and safeguarding returns.

Use it freely. If you want the daily reconciliation built and evidenced rather than described, my details are at the end of the document.

## 2. A job-application workbench driven by a local model

`workbench/`

A small, dependency-free toolkit that runs a job search from one source of truth (`MASTER_PROFILE.md`), using either a local model through Ollama or a cloud coding agent:

- `scripts/jobprep.py` — a chat session that loads the profile plus a task prompt (role fit, CV tailoring, cover letter, form answers, interview prep, mock interview) and keeps research in context across steps. Web search with provider fallback. Works with any Ollama model.
- `prompts/` — one prompt per task, written to behave identically on a 26B local model and on Claude Code or Codex. `simple-english.md` is the writing rule set (condensed ASD-STE100) that every tool loads so that all drafts read the same way.
- `templates/` — LaTeX CV and cover-letter skeletons with placeholders.
- `automation/` — three scripts that run daily and write one Markdown report: diff the FCA e-money and payment-services registers (newly authorised firms are prospects), poll Greenhouse, Lever, Ashby and Workable boards and score new adverts against the profile with the local model, and draft outreach from a fixed template into an outbox for review. Nothing is sent or submitted automatically; that is a design decision, not a limitation.

`MASTER_PROFILE.template.md` shows the structure the tools expect. Fill it with your own facts. The rule at the top of that file, that nothing may be invented downstream, is the reason the whole thing works.

## Contact

lee.hantae@gmail.com · [linkedin.com/in/dhl84](https://www.linkedin.com/in/dhl84/)
