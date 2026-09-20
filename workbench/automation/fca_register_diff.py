"""Daily: download the FCA e-money and PSD register extracts, report newly authorised
firms and status changes, and add new authorised EMIs/PIs to the target list as Tier 1.

A firm authorised in the last few weeks has no reconciliation process yet and its first
audit period starts now. That is the warmest cold prospect there is.
"""
import csv, io, sys
from common import *

SOURCES = {
    "emi": ("https://register.fca.org.uk/servlet/servlet.FileDownload?file=015b0000006CWmx", "Emoney Register Status", "Emoney Status Effective Date"),
    "psd": ("https://register.fca.org.uk/servlet/servlet.FileDownload?file=015b0000006CXC7", "PSD Firm Status", "PSD Status Effective Date"),
}
IN_SCOPE = ("Authorised Electronic Money Institution", "Small Electronic Money Institution", "Authorised Payment Institution")


def parse(raw, status_col, date_col):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
    required = {"FRN", "Firm", status_col, date_col}
    headers = reader.fieldnames or []
    if not required.issubset(headers) or len(headers) != len(set(headers)):
        raise ValueError("missing or duplicate register columns")
    rows = {}
    for row in reader:
        if None in row or any(row[c] is None for c in required):   # extra fields, or a short row; the trailing "Data listed here..." column is legitimately empty
            raise ValueError("malformed register row")
        frn = row["FRN"].strip()
        if not frn or not row["Firm"].strip() or frn in rows:
            raise ValueError("blank FRN/firm or duplicate FRN")
        rows[frn] = row
    if not rows:
        raise ValueError("empty register")
    return rows


def main():
    lines = []
    targets = read_targets()
    known_frn = {r["frn"] for r in targets}
    added = 0
    for key, (url, status_col, date_col) in SOURCES.items():
        try:
            raw = fetch(url)
        except Exception as e:  # noqa: BLE001
            lines.append(f"- {key.upper()} register: download failed ({e})")
            continue
        prev = load_json(f"fca_{key}_prev.json", {})
        try:
            cur = parse(raw, status_col, date_col)
            missing = prev.keys() - cur.keys()
            if len(missing) > 0.01 * len(prev):
                # a genuine removal is rare and small; a large gap means a truncated extract
                raise ValueError(f"{len(missing)} stored FRNs missing; review removals before replacing the baseline")
            for frn in sorted(missing):
                lines.append(f"  - REMOVED {prev[frn].get('firm', '')} (FRN {frn}) no longer in the extract")
            if any(p.get("status") and not cur[frn][status_col].strip() for frn, p in prev.items() if frn in cur):
                raise ValueError("previously populated status is now blank")
        except (ValueError, csv.Error) as e:
            lines.append(f"- {key.upper()} register: invalid download ({e}); baseline kept, no diff today")
            continue
        new, changed = [], []
        for frn, r in cur.items():
            st = r.get(status_col, "").strip()
            date = (r.get(date_col) or "")[:10]
            p = prev.get(frn)
            if p is None:
                if prev:  # not first run
                    new.append((frn, r["Firm"], st, date))
            elif p.get("status") != st:
                changed.append((frn, r["Firm"], p.get("status"), st, date))
        save_json(f"fca_{key}_prev.json", {frn: {"firm": r["Firm"], "status": r.get(status_col, "").strip()} for frn, r in cur.items()})
        if not prev:
            lines.append(f"- {key.upper()} register: baseline stored ({len(cur)} firms). Changes appear from tomorrow.")
            continue
        lines.append(f"- {key.upper()} register: {len(cur)} firms, {len(new)} new, {len(changed)} status changes")
        for frn, firm, st, date in new:
            lines.append(f"  - NEW {firm} (FRN {frn}) {st} {date}")
            if st in IN_SCOPE and st.startswith("Authorised") and frn not in known_frn:
                targets.append({"tier": "1", "firm": firm, "type": "EMI" if key == "emi" else "API", "frn": frn,
                                "authorised": date, "why_now": f"NEW on register {TODAY}: first audit period starts now; no legacy process",
                                "status": "not started"})
                known_frn.add(frn); added += 1
        for frn, firm, old, st, date in changed:
            flag = " (in target list)" if frn in known_frn else ""
            lines.append(f"  - CHANGE {firm} (FRN {frn}): {old} -> {st} {date}{flag}")
    if added:
        write_targets(targets)
        lines.append(f"- Added {added} newly authorised firm(s) to target-list.csv as Tier 1")
    append_report("FCA register", "\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
