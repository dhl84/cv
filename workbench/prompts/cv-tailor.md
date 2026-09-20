# TASK: Tailor a CV

You are producing a tailored CV for David H. Lee from the MASTER PROFILE already in context.

## Rules
- Use **only** facts from the MASTER PROFILE. No new employers, dates, figures or tools.
- Tailoring = selecting, ordering and re-weighting existing bullets. Not rewriting history.
- Obey the §11 Style guide: British English, dense bullets, ownership verbs, hedged numbers,
  no buzzwords.
- Fits 2 pages: summary ~120 words, competencies ~110 words, 14–20 bullets total.

## Method
1. **Parse the job ad.** Extract, as a list: the 6–10 must-have requirements, the
   nice-to-haves, the named tools/systems, the seniority signal, and the underlying problem
   the company is hiring to solve.
2. **Pick the archetype** (§2 A–E) that best matches. State which and why in one line.
3. **Map requirements to evidence.** Produce a table: `Requirement | Best evidence | Where it
   appears on the CV`. Any requirement with no evidence gets a `GAP:` line and a §12
   honest-framing suggestion — never a fabricated bullet.
4. **Draft the headline.** Adapt the archetype headline so it uses the job ad's own
   vocabulary where the underlying fact is genuinely the same thing.
5. **Draft the summary.** Start from the archetype summary; re-order clauses so the first
   sentence after the credentials line is the achievement this employer cares about most.
6. **Draft the Core Competencies block.** Four pipe-separated groups, each headed in bold.
   Front-load the job ad's terminology where §7 supports it.
7. **Select experience bullets.** Ledger Rocket 2–3, Genius Sports 1–2, Apron 3–5,
   Revolut FP&A 2–3, Revolut Ops 2–4, CAPCO 1, Bregal 1–2, KPMG 1, Trustee 1 (drop the
   Trustee section if space is tight and governance is irrelevant).
8. **Sanity-check against the style guide** before output.

## Output
```
## 1. Job ad analysis
## 2. Archetype chosen + why
## 3. Requirement → evidence map (table, GAPs flagged)
## 4. Headline
## 5. Summary
## 6. Core competencies
## 7. Experience bullets, by role, in CV order
## 8. Notes for David (what was dropped, what to verify, ATS keywords missed)
```

If asked for LaTeX, emit a complete `.tex` file based on `templates/cv-template.tex`,
escaping `&` as `\&`, `%` as `\%`, `£` as `\pounds`, `#` as `\#`, and using `--` for
en-dashes. If asked for Word, emit clean Markdown with `#`/`##` headings and `-` bullets,
ready for pandoc.
