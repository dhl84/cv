# Daily income automations

Three scripts run once a day, write one Markdown report to `gtm/daily/YYYY-MM-DD.md`, and stop. No script sends or submits anything. You read the report over coffee and run `jobprep.ps1 -Mode fit` on the roles that scored well.

The plan is inbound-led (see §06 of the GTM pack), so the daily run drafts no outreach. `daily.ps1` passes `-Drafts 0`, and the register diff is a signal for the partner briefing and for the timing of the next published page. Draft an email by hand for a firm where you hold a contact. Draft one when a partner asks you to write to a named client.

| Script | What it does | Needs the GPU |
|---|---|---|
| `fca_register_diff.py` | Downloads the FCA e-money and PSD register extracts, diffs them against yesterday, reports newly authorised firms and status changes, and adds new authorised EMIs and PIs to `target-list.csv` as Tier 1. | No |
| `job_scan.py` | Polls the Greenhouse, Lever, Ashby and Workable boards listed in `watchlist.json`, keeps finance titles in London, scores each new advert 0 to 10 against `MASTER_PROFILE.md` sections 2, 7 and 10 with the local model, and flags whether the advert meets the £80k floor. | Yes (add `--no-score` to skip) |
| `draft_outreach.py N` | Takes the next N targets with status `not started`, drafts the prospect email from `prospect-template.md` with the local model, writes each draft to `gtm/outbox/`, and marks the row `drafted`. Default N is 0, so a plain run does nothing. Pass N to draft on purpose. | Yes |

`daily.ps1` runs the three in order and starts Ollama if it is not running. `register_task.ps1` puts `daily.ps1` in Windows Task Scheduler at 07:00.

## Set up on the desktop (RTX 5090)

1. Make sure that the `gemma4-se` model exists. It is `gemma4:26b-a4b-it-qat` with the Simple English rules as its system prompt. If `ollama list` does not show it, run `ollama create gemma4-se -f ..\..\scripts\Modelfile.simple-english` from this folder.
2. Run the scripts once by hand to store the register baseline and the seen-jobs list:

   ```powershell
   cd <repo>\workbench\automation
   .\daily.ps1 -Open
   ```

3. Register the daily task:

   ```powershell
   .\register_task.ps1            # 07:00 daily; -At "06:30" to change
   Start-ScheduledTask -TaskName cv-daily-income   # test it now
   ```

4. Read `gtm\daily\<today>.md`. The first run reports a baseline only; changes appear from the second run.

The model is loaded on the first call each day, which takes about a minute on the 5090. Scoring 20 adverts takes two to three minutes. Drafting one email, when you ask for one, takes under a minute.

## Set up on the MacBook (M4 Max, 48 GB)

The scripts are the same. Ollama on the Mac holds the 15 GB model in unified memory.

```sh
brew install ollama && ollama serve &
ollama pull gemma4:26b-a4b-it-qat
ollama create gemma4-se -f scripts/Modelfile.simple-english
cd gtm/automation && python3 fca_register_diff.py && python3 job_scan.py
```

To run it daily, put a `launchd` plist in `~/Library/LaunchAgents/` that runs `daily.sh` (the three `python3` lines above) at 07:00, or run it by hand when you open the laptop. Keep the state folder in the repo so that both machines share the seen-jobs list and the register baseline: commit `gtm/automation/state/` to `cv_private` after each run, or point `DATA` in `common.py` at a synced folder.

## Tuning

Jobs with a saved score of -1 remain pending. A normal scan retries them while they
are still on the board and match the filters. `--no-score` records new jobs without
scoring them; the next normal scan can score them. Completed scores from 0 to 10
are skipped. Ashby compensation is passed separately from the shortened advert.

Register downloads must contain the expected columns and valid, unique FRNs.
If a download loses any stored FRN or clears a previously populated status, the
script keeps the baseline and skips that source's changes. Genuine removals need
manual review before replacing the baseline. These checks cannot prove that an
initial download is complete.

Run offline regression checks from the project root with
`python -B -m unittest discover -s tests -v`. They do not call a model or website.

- `watchlist.json`: add a company by its ATS slug. A wrong slug costs nothing (404 is skipped). To find the slug, open the company's careers page and read the URL after `boards.greenhouse.io/`, `jobs.lever.co/`, `jobs.ashbyhq.com/` or `apply.workable.com/`.
- `title_regex` and `exclude_regex` in the same file control which titles survive. The location filter passes adverts with no stated location, so expect some non-UK noise from global boards; the score sorts it out.
- `JOBPREP_MODEL` and `OLLAMA_HOST` environment variables override the model and server.
- Outreach drafting is off by default. To draft on one day, run `daily.ps1 -Drafts 3`.

## What it does not do

It does not scrape LinkedIn or Indeed (both forbid it and both will ban the account). It does not send email. It does not apply to jobs. Those three things stay with you, on purpose: the report is designed to take you fifteen minutes and leave every outward action as a decision you made.
