"""Offline regression checks; no live model, network or state writes."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
AUTOMATION = next(d for d in (ROOT / "gtm" / "automation", ROOT / "workbench" / "automation") if (d / "job_scan.py").exists())
sys.path.insert(0, str(AUTOMATION))
import job_scan as jobs
import fca_register_diff as fca


class JobTests(unittest.TestCase):
    def run_scan(self, state, no_score=False, result=8):
        job = dict(id="test:1", title="Finance Manager", company="test", location="London", desc="Finance", url="test", posted="")
        with patch.multiple(jobs, PROVIDERS={"test": lambda _: [job]}, WL={"test": ["test"]}), \
             patch.object(jobs, "load_json", return_value=copy.deepcopy(state)), \
             patch.object(jobs, "save_json") as save, \
             patch.object(jobs, "profile_section", return_value=""), \
             patch.object(jobs, "score", return_value=(result, "unknown", "")) as score, \
             patch.object(jobs, "append_report"), \
             patch.object(sys, "argv", ["scan"] + (["--no-score"] if no_score else [])), \
             contextlib.redirect_stdout(io.StringIO()):
            jobs.main()
            return save.call_args.args[1], score.call_count

    def test_old_failed_scores_retry_and_completed_scores_skip(self):
        state, calls = self.run_scan({"test:1": {"score": -1}})
        self.assertEqual(calls, 1)
        self.assertEqual(state["test:1"]["score"], 8)
        self.assertEqual(self.run_scan(state)[1], 0)

    def test_no_score_remains_pending(self):
        state, calls = self.run_scan({}, no_score=True)
        self.assertEqual(calls, 0)
        self.assertEqual(self.run_scan(state, no_score=True)[1], 0)
        self.assertEqual(self.run_scan(state)[1], 1)

    def test_failure_remains_retryable(self):
        state, _ = self.run_scan({}, result=-1)
        self.assertEqual(self.run_scan(state)[1], 1)

    def test_salary_survives_long_description(self):
        for length in (5100, 7000):
            raw = {"jobs": [{"id": "1", "title": "Finance Manager", "descriptionPlain": "x" * length,
                             "compensation": {"compensationTierSummary": "GBP 100000-120000"}}]}
            with patch.object(jobs, "fetch", return_value=json.dumps(raw)), \
                 patch.object(jobs, "ollama", return_value="SCORE: 8\nFLOOR: yes\nBAND: GBP 100000-120000\nWHY: match") as model:
                self.assertEqual(jobs.score(next(jobs.ashby("test")), "")[0], 8)
                self.assertIn("Compensation: GBP 100000-120000", model.call_args.args[0])

    def test_invalid_model_score_is_pending(self):
        job = dict(title="Finance", company="test", location="London", desc="")
        for output in ("", "SCORE: 11", "SCORE: 8.5", "SCORE: -1"):
            with patch.object(jobs, "ollama", return_value=output):
                self.assertEqual(jobs.score(job, "")[0], -1)


class RegisterTests(unittest.TestCase):
    def run_register(self, raw, prev):
        with patch.object(fca, "SOURCES", {"test": ("unused", "Status", "Date")}), \
             patch.object(fca, "fetch", return_value=raw), \
             patch.object(fca, "load_json", return_value=prev), \
             patch.object(fca, "save_json") as save, \
             patch.object(fca, "read_targets", return_value=[]), \
             patch.object(fca, "write_targets") as targets, \
             patch.object(fca, "append_report"), contextlib.redirect_stdout(io.StringIO()):
            fca.main()
            return save, targets

    def test_missing_firms_cannot_replace_baseline(self):
        prev = {str(i): {"firm": "Firm", "status": "Active"} for i in range(10)}
        for ids in (range(6), range(1, 11)):
            raw = ("FRN,Firm,Status,Date\n" + "".join(f"{i},Firm,Active,2026-01-01\n" for i in ids)).encode()
            save, targets = self.run_register(raw, prev)
            save.assert_not_called()
            targets.assert_not_called()

    def test_small_removal_is_reported_and_baseline_replaced(self):
        prev = {str(i): {"firm": "Firm", "status": "Active"} for i in range(300)}
        raw = ("FRN,Firm,Status,Date\n" + "".join(f"{i},Firm,Active,2026-01-01\n" for i in range(1, 300))).encode()
        save, _ = self.run_register(raw, prev)
        save.assert_called_once()
        self.assertNotIn("0", save.call_args.args[1])

    def test_invalid_registers_preserve_baseline(self):
        prev = {"1": {"firm": "Firm", "status": "Active"}}
        for raw in (b"FRN,Firm,Date\n1,Firm,2026\n", b"FRN,Firm,Status,Date\n1,Firm,,2026\n",
                    b"<html>Error</html>", b"FRN,Firm,Status,Date\n1,Firm,Active\n",
                    b"FRN,Firm,Status,Date\n1,Firm,Active,2026\n1,Firm,Active,2026\n"):
            save, targets = self.run_register(raw, prev)
            save.assert_not_called()
            targets.assert_not_called()

    def test_valid_new_firm_is_added(self):
        raw = b"FRN,Firm,Status,Date\n1,Old,Active,2026\n2,New,Authorised Payment Institution,2026\n"
        save, targets = self.run_register(raw, {"1": {"firm": "Old", "status": "Active"}})
        save.assert_called_once()
        self.assertEqual(targets.call_args.args[0][0]["frn"], "2")

    def test_initial_baseline_does_not_add_prospects(self):
        save, targets = self.run_register(b"FRN,Firm,Status,Date\n1,Firm,Authorised Payment Institution,2026\n", {})
        save.assert_called_once()
        targets.assert_not_called()


class LauncherTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell unavailable")
    def test_context_default_environment_and_explicit_override(self):
        script = """
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Get-ChildItem -Path $env:TEST_ROOT -Recurse -Filter jobprep.ps1 | Select-Object -First 1).FullName, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw $errors[0] }
$block = [scriptblock]::Create($ast.ParamBlock.Extent.Text + '; $Ctx')
if ($env:TEST_EXPLICIT) { & $block -Ctx 8192 } else { & $block }
"""
        for env_ctx, explicit, expected in (("", "", "49152"), ("65536", "", "65536"), ("65536", "yes", "8192")):
            env = dict(os.environ, TEST_ROOT=str(ROOT), JOBPREP_CTX=env_ctx, TEST_EXPLICIT=explicit)
            result = subprocess.run(["pwsh", "-NoProfile", "-Command", script], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), expected)


if __name__ == "__main__":
    unittest.main()
