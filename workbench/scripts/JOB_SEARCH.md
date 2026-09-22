# Job link discovery

Run without loading a model:

```powershell
.\scripts\jobprep.ps1 -Company 'Example employer' -Role 'Finance Manager' -FindJobs
.\scripts\jobprep.ps1 -Company 'Example employer' -Role 'Finance Manager' -FetchJd 'https://example.com/careers/role'
```

Equivalent Python flags are `--find-jobs` and `--fetch-jd URL`.
In a session use `/find-jobs` or `/fetch URL`.

Open the application's `job-links.html` for candidate URLs and browser search links.
Only employer sources registered in `scripts/employer-sites.json` are accepted.
This records confirmed careers URLs, employer-specific ATS paths, aliases and known
roles. Unknown employers return no matches until their site is verified and registered.
Workable acceptance is restricted to the employer's tenant, not the whole domain.
Search queries target registered sites. Third-party listings are rejected even if
their titles match. Missing roles fall back to the labelled employer careers page.
Known links do not prove that a vacancy is open.
`job-search.json` records the attempts. When providers return no relevant matches, use
the browser searches; the tool does not invent job URLs.

Fetching saves `job-source.url` and `job-ad-fetched.md`. Review the extracted text and
copy it to `job-ad.md` or import it with `-Jd` / `--jd`. Existing pasted adverts are
preserved. Use `/reload` after editing. The model reads imported text, not URLs by itself.

Some sites require JavaScript or block retrieval. Copying the advert manually remains
supported. Fetch success alone does not prove the response contains the complete ad.
