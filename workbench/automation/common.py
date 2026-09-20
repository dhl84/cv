"""Shared helpers for the daily income automations."""
import csv, json, os, sys, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # cv/
GTM = os.path.join(ROOT, "gtm")
DATA = os.path.join(GTM, "automation", "state")
DAILY = os.path.join(GTM, "daily")
OUTBOX = os.path.join(GTM, "outbox")
TARGETS = os.path.join(GTM, "target-list.csv")
PROFILE = os.path.join(ROOT, "MASTER_PROFILE.md")
RULES = os.path.join(ROOT, "prompts", "simple-english.md")
for d in (DATA, DAILY, OUTBOX):
    os.makedirs(d, exist_ok=True)

OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
if not OLLAMA.startswith("http"):
    OLLAMA = "http://" + OLLAMA
MODEL = os.environ.get("JOBPREP_MODEL", "gemma4-se")

TODAY = datetime.date.today().isoformat()
REPORT = os.path.join(DAILY, f"{TODAY}.md")


def read(p, default=""):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return default


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def append_report(section, body):
    """Append a section to today's report, creating it with a header on first use."""
    if not os.path.exists(REPORT):
        write(REPORT, f"# Daily income report, {TODAY}\n\n")
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(f"## {section}\n\n{body.rstrip()}\n\n")


def load_json(name, default):
    return json.loads(read(os.path.join(DATA, name), json.dumps(default)))


def save_json(name, obj):
    write(os.path.join(DATA, name), json.dumps(obj, indent=1, ensure_ascii=False))


def fetch(url, timeout=60, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (cv-automation)", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def read_targets():
    with open(TARGETS, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows


def write_targets(rows):
    cols = ["tier", "firm", "type", "frn", "authorised", "why_now", "status",
            "contact_name", "contact_role", "channel", "last_touch", "notes"]
    with open(TARGETS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def ollama(prompt, system="", model=None, temperature=0.3, num_ctx=32768, timeout=600):
    """One-shot chat completion against the local Ollama server. Returns text or ''."""
    body = json.dumps({
        "model": model or MODEL,
        "messages": ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": temperature, "num_ctx": num_ctx},
    }).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/chat", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["message"]["content"].strip()
    except Exception as e:  # noqa: BLE001
        print(f"  ollama failed: {e}", file=sys.stderr)
        return ""


def profile_section(n):
    """Return section n of MASTER_PROFILE.md (text between '## n.' and the next '## ')."""
    t = read(PROFILE)
    start = t.find(f"\n## {n}.")
    if start < 0:
        return ""
    end = t.find("\n## ", start + 5)
    return t[start:end if end > 0 else None]
