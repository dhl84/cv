"""Daily: poll public ATS job boards (Greenhouse, Lever, Ashby, Workable) for finance roles
in London that match the title filter, score each new one against MASTER_PROFILE with the
local model, and write a ranked shortlist to today's report.

Nothing is applied for automatically. The shortlist is the input to `jobprep.ps1 -Mode fit`.
"""
import json, re, sys, html
from common import *

WL = json.loads(read(os.path.join(GTM, "automation", "watchlist.json")))
TITLE = re.compile(WL["title_regex"])
LOC = re.compile(WL["location_regex"])
EXCL = re.compile(WL["exclude_regex"])


def strip_html(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def greenhouse(slug):
    d = json.loads(fetch(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"))
    for j in d.get("jobs", []):
        yield {"id": f"gh:{slug}:{j['id']}", "company": slug, "title": j["title"], "location": (j.get("location") or {}).get("name", ""),
               "url": j["absolute_url"], "desc": strip_html(j.get("content", ""))[:6000], "posted": j.get("updated_at", "")[:10]}


def lever(slug):
    d = json.loads(fetch(f"https://api.lever.co/v0/postings/{slug}?mode=json"))
    for j in d:
        cats = j.get("categories", {})
        yield {"id": f"lv:{slug}:{j['id']}", "company": slug, "title": j["text"], "location": cats.get("location", ""),
               "url": j["hostedUrl"], "desc": strip_html(j.get("descriptionPlain") or j.get("description", ""))[:6000], "posted": ""}


def ashby(slug):
    d = json.loads(fetch(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"))
    for j in d.get("jobs", []):
        comp = (j.get("compensation") or {}).get("compensationTierSummary", "")
        yield {"id": f"ab:{slug}:{j['id']}", "company": slug, "title": j["title"], "location": j.get("location", ""),
               "url": j.get("jobUrl", ""), "desc": strip_html(j.get("descriptionPlain") or j.get("descriptionHtml", ""))[:6000], "compensation": comp,
               "posted": (j.get("publishedAt") or "")[:10]}


def workable(slug):
    d = json.loads(fetch(f"https://apply.workable.com/api/v3/accounts/{slug}/jobs", headers={"Content-Type": "application/json"}))
    for j in d.get("results", []):
        loc = j.get("location", {}) or {}
        yield {"id": f"wk:{slug}:{j.get('shortcode')}", "company": slug, "title": j["title"],
               "location": ", ".join(x for x in [loc.get("city"), loc.get("country")] if x),
               "url": f"https://apply.workable.com/{slug}/j/{j.get('shortcode')}/", "desc": strip_html(j.get("description", ""))[:6000], "posted": (j.get("published") or "")[:10]}


PROVIDERS = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby, "workable": workable}

SCORE_SYSTEM = (
    "You score job adverts for the candidate. Use only the profile below. Reply with exactly four lines:\n"
    "SCORE: <0-10>\nFLOOR: <yes|no|unknown> (does the advert's stated or likely base salary meet the salary floor stated in the profile?)\n"
    "BAND: <the stated salary or range, or 'not stated'; append 'TARGET' if the top of the band meets the profile's target salary>\n"
    "WHY: <one sentence, under 30 words, naming the strongest match and the biggest gap>\n\n"
)


def score(job, profile_text):
    prompt = (f"Title: {job['title']}\nCompany: {job['company']}\nLocation: {job['location']}\n"
              f"Compensation: {job.get('compensation') or 'not stated'}\n\nAdvert:\n{job['desc'][:5000]}")
    out = ollama(prompt, system=SCORE_SYSTEM + profile_text, temperature=0.1)
    m = re.search(r"^SCORE: *([0-9]|10) *$", out, re.MULTILINE)
    f = re.search(r"FLOOR:\s*(\w+)", out)
    w = re.search(r"WHY:\s*(.+)", out)
    b = re.search(r"BAND:\s*(.+)", out)
    why = w.group(1).strip() if w else out[:200]
    if b and "not stated" not in b.group(1).lower():
        why += f" Band: {b.group(1).strip()}"
    return (int(m.group(1)) if m else -1, f.group(1).lower() if f else "unknown", why)


def main():
    seen = load_json("seen_jobs.json", {})
    no_score = "--no-score" in sys.argv
    profile_text = "# PROFILE\n" + profile_section(2)[:6000] + "\n" + profile_section(7) + "\n" + profile_section(10)
    found, errors = [], 0
    for prov, fn in PROVIDERS.items():
        for slug in WL.get(prov, []):
            try:
                for j in fn(slug):
                    previous = seen.get(j["id"], {})
                    completed = type(previous.get("score")) is int and 0 <= previous["score"] <= 10
                    if completed or (no_score and j["id"] in seen) or not TITLE.search(j["title"]) or EXCL.search(j["title"]):
                        continue
                    if j["location"] and not LOC.search(j["location"]) and not LOC.search(j["desc"][:800]):
                        continue
                    found.append(j)
            except Exception:  # noqa: BLE001  (404 for wrong slug, rate limit, etc.)
                errors += 1
    print(f"{len(found)} matching roles new or awaiting scoring, {errors} boards unreachable")
    scored = []
    for j in found:
        s, floor, why = score(j, profile_text) if not no_score else (-1, "unknown", "")
        if 0 <= s <= 10 or no_score:
            seen[j["id"]] = {"date": TODAY, "score": s, "title": j["title"], "company": j["company"]}
        scored.append((s, floor, why, j))
        print(f"  {s:>2} {floor:<7} {j['company']:<16} {j['title']}")
    save_json("seen_jobs.json", seen)
    scored.sort(key=lambda x: -x[0])
    lines = [f"{len(found)} roles new or awaiting scoring matched the title filter; {errors} boards unreachable (wrong slug or rate limit).", ""]
    for s, floor, why, j in scored:
        lines.append(f"- **{s}/10** {'(floor ok)' if floor=='yes' else '(floor '+floor+')'} [{j['title']}]({j['url']}) at {j['company']}, {j['location'] or 'location unstated'}{', posted '+j['posted'] if j['posted'] else ''}  \n  {why}")
    if not scored:
        lines.append("Nothing new today.")
    append_report("Job scan", "\n".join(lines))


if __name__ == "__main__":
    main()
