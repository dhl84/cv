# TASK: Fill in a job application form

Produce copy-paste-ready answers for an online application (Workday, Greenhouse, Lever,
Ashby, SmartRecruiters, Taleo, or a bespoke form).

## Inputs
- MASTER PROFILE §1, §3, §8, §9 (identity, timeline, education, standard answers).
- The job ad.
- Either: the list of form fields David pasted, or — if none given — produce the **standard
  Workday-style set** below.

## Standard set (produce all of these when no field list is given)

**Personal**
Legal name · preferred name · email · phone · address · country · right to work ·
sponsorship required · how did you hear about us · previously employed here

**Work experience** — for each of the 9 entries in §3, in reverse-chronological order:
```
Job title:
Company:
Location:
From (MM/YYYY):    To (MM/YYYY):    I currently work here: Y/N
Description (Workday truncates around 500–1000 chars — write to 600):
```
Dates: where the profile shows a year only, use `01/YYYY` for start and `12/YYYY` for end
unless a month is given, and add a `VERIFY:` note so David corrects it.

**Education** — the three entries in §8, with institution, degree, field, dates, grade.

**Skills** — a comma-separated list of 20–30 terms, ordered by relevance to *this* job ad,
drawn only from §7.

**Free text** — draft answers to whichever of these the form asks:
- Why do you want to work here? (150 words)
- Why are you leaving your current role? (60 words)
- What makes you a strong fit? (100 words / 500 chars — give both lengths)
- Describe a relevant achievement. (150 words)
- Salary expectation · notice period · earliest start date
- Anything else we should know? (usually: leave blank, or one line)

**Voluntary/EEO** — list the fields, mark each `David's choice — decline or answer`.
Do not answer these on his behalf.

## Rules
- Respect stated character limits exactly; give the character count after each answer.
- Plain text only — these boxes strip formatting. No markdown, no em-dashes that break
  encoding, no smart quotes.
- Anything not in the MASTER PROFILE gets `VERIFY:` — especially dates, salary and notice.
- Keep the same facts across every field; recruiters cross-check the form against the CV.

## Output
One block per field, formatted as:
```
### <Field label>
<answer>
[chars: N]
```
End with a `## VERIFY before submitting` checklist of every uncertain item.
