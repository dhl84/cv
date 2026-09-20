"""Daily: take the next few Tier 1/2 targets with status 'not started', draft a prospect
email for each with the local model from the approved template, and put the drafts in
gtm/outbox/ for review. Marks the row 'drafted'. Nothing is sent by this script.

Usage: python draft_outreach.py [N]   (default 0; the plan is inbound-led, so pass N by hand)
"""
import re, sys
from common import *

TEMPLATE = read(os.path.join(GTM, "automation", "prospect-template.md"))

SYSTEM = (
    "You draft one short outreach email for David H. Lee, a finance lead who sells safeguarding "
    "reconciliation remediation to UK payment and e-money firms. Use the TEMPLATE as the fixed "
    "structure and register. Change only the bracketed fields and the one sentence that names the "
    "firm-specific fact. Never invent facts about the firm beyond what is given. Never add adjectives, "
    "flattery, or a second call to action. British English. Output only the email, starting with 'Subject:'.\n\n"
    + read(RULES)
)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if n <= 0:
        return
    rows = read_targets()
    todo = [r for r in rows if r["tier"] in ("1", "2") and r["status"].strip() == "not started"][:n]
    done = []
    for r in todo:
        prompt = (f"TEMPLATE:\n{TEMPLATE}\n\nFIRM: {r['firm']}\nTYPE: {'e-money institution' if r['type']=='EMI' else 'payment institution'}\n"
                  f"FRN: {r['frn']}\nAUTHORISED: {r['authorised'] or 'unknown'}\nWHAT WE KNOW: {r['why_now']}\n"
                  f"CONTACT: {r['contact_name'] or '[Name]'} ({r['contact_role'] or 'CFO or designated safeguarding individual'})")
        email = ollama(prompt, system=SYSTEM, temperature=0.4)
        if not email:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", r["firm"].lower()).strip("-")
        path = os.path.join(OUTBOX, f"{TODAY}-{slug}.md")
        write(path, f"<!-- REVIEW BEFORE SENDING. Firm: {r['firm']} FRN {r['frn']} tier {r['tier']} -->\n\n{email}\n")
        r["status"] = "drafted"; r["last_touch"] = TODAY; r["channel"] = r["channel"] or "email"
        done.append((r["firm"], path))
        print(f"  drafted {r['firm']} -> {path}")
    if done:
        write_targets(rows)
    append_report("Outreach drafts", "\n".join(f"- {f}: `{p}`" for f, p in done) or "No drafts today (nothing left with status 'not started', or N=0).")


if __name__ == "__main__":
    main()
