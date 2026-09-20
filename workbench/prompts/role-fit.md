# TASK: Evaluate role fit

Score a job ad against David's MASTER PROFILE and preferences (§10). Be blunt — the
purpose is to stop him wasting time on bad-fit roles, not to cheerlead.

## Method
1. Extract the job ad's requirements into three buckets: **must-have**, **nice-to-have**,
   **implied but unstated** (e.g. "reporting to the Group FC" implies statutory experience).
2. Score each requirement: `STRONG` (direct, evidenced, recent) / `PARTIAL` (adjacent or
   dated) / `NONE`.
3. Compute two separate scores out of 10:
   - **Can he do it?** — capability match.
   - **Does he want it?** — match against §10 preferences.
4. Identify the **one thing most likely to get him rejected** and how to pre-empt it in the
   CV or cover letter.
5. Identify the **one thing most likely to get him hired** — the asymmetric advantage.
6. Flag any deal-breaker from §10.

## Output
```
## Verdict: APPLY / APPLY WITH CAVEAT / SKIP
One-line reason.

## Requirement scorecard
| Requirement | Must/Nice | Score | Evidence |

## Capability fit: X/10 — <two lines>
## Desirability fit: X/10 — <two lines>

## Biggest rejection risk
## Biggest asymmetric advantage
## Deal-breakers triggered
## If applying: archetype to use, and the three things the CV must lead with
## Questions David should ask before investing time (screening call questions)
```
