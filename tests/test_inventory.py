"""Offline checks for the evidence inventory. No network, no source writes."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import unittest.mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evidence"))
import inventory


class InventoryTests(unittest.TestCase):
    def build(self):
        source = Path(tempfile.mkdtemp()) / "bundle"
        (source / "sub").mkdir(parents=True)
        (source / "note.md").write_text("# Statement\nBalance 100.00\n", encoding="utf-8")
        (source / "sub" / "ledger.csv").write_text("date,amount\n2026-01-01,100.00\n", encoding="utf-8")
        (source / "scan.jpg").write_bytes(b"\xff\xd8\xff\xe0not-an-image")
        (source / "__pycache__").mkdir()
        (source / "__pycache__" / "x.pyc").write_bytes(b"cache")
        (source / "notebook.ipynb").write_text(json.dumps(
            {"cells": [{"cell_type": "code", "source": ["DROP SCHEMA public;\n"]}]}), encoding="utf-8")
        return source, Path(tempfile.mkdtemp()) / "out"

    def test_hashes_files_and_skips_caches(self):
        source, out = self.build()
        records = inventory.inventory(source, out)
        files = {r["file"]: r for r in records}
        self.assertEqual(set(files), {"note.md", "notebook.ipynb", "scan.jpg", "sub/ledger.csv"})
        expected = hashlib.sha256((source / "note.md").read_bytes()).hexdigest()
        self.assertEqual(files["note.md"]["sha256"], expected)
        self.assertEqual(files["scan.jpg"]["status"], "inventory only; no extractor for this format")

    def test_notebook_source_is_read_but_not_executed(self):
        source, out = self.build()
        records = inventory.inventory(source, out)
        record = next(r for r in records if r["file"] == "notebook.ipynb")
        self.assertEqual(record["status"], "cell source read; not executed")
        self.assertIn("DROP SCHEMA public;", (out / record["extract"]).read_text(encoding="utf-8"))

    def test_manifest_and_index_list_every_file(self):
        source, out = self.build()
        records = inventory.inventory(source, out)
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["files"]), len(records))
        index = (out / "index.md").read_text(encoding="utf-8")
        for record in records:
            self.assertIn(record["file"], index)

    def test_source_directory_is_unchanged(self):
        source, out = self.build()
        before = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in source.rglob("*") if p.is_file()}
        inventory.inventory(source, out)
        after = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in source.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_unreadable_file_is_reported_and_the_run_continues(self):
        source, out = self.build()
        broken = source / "broken.ipynb"
        broken.write_text("{not json", encoding="utf-8")
        records = inventory.inventory(source, out)
        record = next(r for r in records if r["file"] == "broken.ipynb")
        self.assertIn("error", record)
        self.assertEqual(record["status"], "not read")
        self.assertEqual(len(records), 5)


    def test_absent_extractor_library_gives_a_status_not_an_error(self):
        source, out = self.build()
        (source / "statement.pdf").write_bytes(b"%PDF-1.4 stub")
        with unittest.mock.patch.dict(sys.modules, {"pypdf": None}):
            records = inventory.inventory(source, out)
        record = next(r for r in records if r["file"] == "statement.pdf")
        self.assertNotIn("error", record)
        self.assertIn("extractor library absent", record["status"])


if __name__ == "__main__":
    unittest.main()
