#!/usr/bin/env python3
"""Inventory a document bundle: hash every file, extract text, execute nothing.

An auditor asks two questions of an evidence bundle: what is in it, and is it
the same bundle you gave me last time. This answers both. It walks a source
directory, records a SHA-256 hash of every file, extracts the readable text of
the document formats it knows, and writes one manifest and one Markdown index.

It never opens a file for writing inside the source directory, never runs a
notebook or a script, and never recalculates a spreadsheet. A spreadsheet
reports its formulas and the values the file already holds, side by side, so a
stale cached value stays visible instead of hidden.

    python3 evidence/inventory.py SOURCE_DIR OUTPUT_DIR

Text extraction needs pypdf, python-docx and openpyxl. Without them the run
still produces the hashes and the file inventory.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path

SKIP = {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache", ".DS_Store"}
TEXT = {".md", ".tex", ".txt", ".csv"}
MAX_EXTRACT_BYTES = 15_000_000


def extract(path, suffix, item):
    """Return the readable text of one file, or an empty string."""
    if suffix == ".pdf":
        from pypdf import PdfReader
        pdf = PdfReader(path)
        item["pages"] = len(pdf.pages)
        text = "\n\n".join(f"--- PAGE {i + 1} ---\n{page.extract_text() or ''}"
                           for i, page in enumerate(pdf.pages))
        item["status"] = "text extracted" if len(text) > 80 * len(pdf.pages) else "scan; needs visual review"
        return text
    if suffix == ".docx":
        from docx import Document
        doc = Document(path)
        rows = [" | ".join(c.text for c in row.cells) for t in doc.tables for row in t.rows]
        item["status"] = "text extracted"
        return "\n".join([p.text for p in doc.paragraphs] + rows)
    if suffix == ".xlsx":
        import openpyxl
        formulas = openpyxl.load_workbook(path, read_only=True, data_only=False)
        stored = openpyxl.load_workbook(path, read_only=True, data_only=True)
        item["sheets"] = formulas.sheetnames
        chunks = []
        for sheet in formulas:
            cached = {c.coordinate: c.value for row in stored[sheet.title] for c in row if c.value is not None}
            chunks.append(f"SHEET {sheet.title} ({sheet.max_row} rows x {sheet.max_column} columns)")
            for row in sheet:
                cells = [f"{c.coordinate}: {c.value}" + (f" [stored={cached.get(c.coordinate)}]" if c.data_type == "f" else "")
                         for c in row if c.value is not None]
                if cells:
                    chunks.append(" | ".join(cells))
        formulas.close()
        stored.close()
        item["status"] = "formulas and stored values read; not recalculated"
        return "\n".join(chunks)
    if suffix == ".ipynb":
        notebook = json.loads(path.read_text(encoding="utf-8"))
        cells = notebook.get("cells", [])
        item["cells"] = len(cells)
        item["status"] = "cell source read; not executed"
        return "\n\n".join(f"--- CELL {i + 1} {c.get('cell_type')} ---\n" + "".join(c.get("source", []))
                           for i, c in enumerate(cells))
    if suffix in TEXT:
        item["status"] = "text read"
        return path.read_text(encoding="utf-8", errors="replace")
    item["status"] = "inventory only; no extractor for this format"
    return ""


def inventory(source, output):
    """Walk source, write the manifest and the index into output, return the records."""
    source, output = Path(source).resolve(), Path(output).resolve()
    extracts = output / "extracts"
    extracts.mkdir(parents=True, exist_ok=True)
    records = []
    for base, dirs, names in os.walk(source):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not (Path(base) / d).is_symlink())
        for name in sorted(names):
            path = Path(base) / name
            if name in SKIP or path.is_symlink():
                continue
            before = path.stat()
            item = {"file": path.relative_to(source).as_posix(), "bytes": before.st_size,
                    "modified": datetime.datetime.fromtimestamp(before.st_mtime).isoformat(timespec="seconds"),
                    "status": "inventory only"}
            records.append(item)
            try:
                item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                if before.st_size <= MAX_EXTRACT_BYTES:
                    text = extract(path, path.suffix.lower(), item)
                    if text:
                        target = extracts / (str(len(records)).zfill(5) + ".txt")
                        target.write_text(text, encoding="utf-8")
                        item["extract"] = target.relative_to(output).as_posix()
                        item["characters"] = len(text)
                else:
                    item["status"] = "large file; hash only"
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    item["status"] = "changed during the read; repeat it"
            except ImportError as error:
                item["status"] = f"hash only; extractor library absent ({error.name})"
            except Exception as error:                      # one unreadable file must not stop the run
                item["error"] = f"{type(error).__name__}: {error}"
                item["status"] = "not read"
    stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    (output / "manifest.json").write_text(
        json.dumps({"source": str(source), "captured": stamp, "files": records}, indent=2), encoding="utf-8")
    lines = [f"# Evidence inventory\n", f"Source: `{source}`. Captured {stamp}. Files: {len(records)}.\n",
             "| File | Bytes | SHA-256 (first 16) | Status | Extract |", "|---|---|---|---|---|"]
    lines += [f"| `{r['file']}` | {r['bytes']} | `{r.get('sha256', '')[:16]}` | {r['status']} | "
              f"{'`' + r['extract'] + '`' if 'extract' in r else ''} |" for r in records]
    (output / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return records


def main():
    parser = argparse.ArgumentParser(description="Hash and read an evidence bundle without executing it.")
    parser.add_argument("source", help="directory that holds the evidence")
    parser.add_argument("output", help="directory for the manifest, the index and the extracts")
    args = parser.parse_args()
    records = inventory(args.source, args.output)
    counts = {}
    for record in records:
        counts[record["status"]] = counts.get(record["status"], 0) + 1
    print(json.dumps({"files": len(records), "status": counts,
                      "errors": [r["file"] for r in records if "error" in r]}, indent=2))


if __name__ == "__main__":
    main()
