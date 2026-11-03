# Curated English challenge pack

This pack adds 21 catalog entries: 7 live web apps, 13 team-generated file
puzzles, and 1 shared-answer OSINT puzzle. Fourteen are selected for the main
180-minute competition; seven are reserves. All participant-facing content is
English. Existing challenges and results are preserved.

## Current delivery state

- Source, player copy, generators, hints, local preview bundles and staging
  script are implemented in branch `codex/curated-english-challenges`.
- `Call Me If You Can` was added to the live site as hidden challenge **26**,
  with its note image, verified answer and an optional free hint.
- The rest of this pack has **not** been deployed to production. The local
  preview bundles contain demonstration flags and must not be uploaded as if
  they were unique team instances.
- No event was started, no old challenge was deleted, and no PR was merged.

## Release plan

| Batch | Time | Challenges |
|---|---|---|
| 1 | Start | Last Edit; Archive Telegram; The Photo Remembers; Dawn Shift; Call Me If You Can |
| 2 | +45 minutes | Forgotten Route; Frontend Pass; Two-Faced Report; The Final Parcel; Known Beginning |
| 3 | +90 minutes | Guard's Message; Not Your Request; Caravan Ledger: Audit; Invisible Ink |
| Reserve | Manual choice only | Trial Account; Template Studio; Machine Language; Close Neighbours; Excess Baggage; Editor's Note; Who Asked? |

Add later batches cumulatively to **one round**. Keep earlier checkboxes
selected. The staging script assigns only batch 1 to a pending round and never
starts it. It does not change the global pause, scoreboard or speed bonus.
For this schedule the recommended speed bonus is zero; set it manually before
the event. Do not restart an already running round to change its duration.

## Local review

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install flask==3.0.3 Pillow==12.2.0
.venv/Scripts/python.exe -m unittest discover -s organizer/tests -v
.venv/Scripts/python.exe organizer/prepare_curated.py
```

Generated previews and player catalog are written to `curated-output/`, ignored
by Git. File puzzles get independent per-team flags through the existing rounds
plugin. The new catalog uses distinct metadata slugs so old generated instances
are not overwritten. OSINT is explicitly a shared public answer.

To preview a web app locally:

```powershell
$env:CHALLENGE='refund-desk'
$env:FLAG='TAIBAH{local_preview_only}'
$env:PORT='8087'
.venv/Scripts/python.exe ctfd-platform/deploy/curated-web/app.py
```

Open `http://127.0.0.1:8087`. This starts only a local preview; production uses
Whale to supply each team's flag. Web unit tests use Flask's test client and do
not prove Docker networking or server capacity.

## Server deployment

1. Export CTFd. Keep the real competition paused while staging.
2. Bring this branch's source onto the server. This pack is based on the main
   branch and does not require the separate event-isolation PR.
3. On **each challenge node**, build the seven image variants:

   ```sh
   sh ctfd-platform/deploy/build-curated.sh
   ```

   These images run as UID 10001 on port 8080. The standard legacy image builder
   skips the shared `curated-web` directory; use the dedicated builder above.

4. Rebuild the CTFd service from `ctfd-platform/` using the existing production
   Compose configuration and `.env`. This installs Pillow and the updated
   generators/frontend. Do not overwrite `.env` or drop database volumes.

   ```sh
   docker compose up -d --build ctfd
   ```

5. Review the staging plan, without writes:

   ```sh
   docker compose exec ctfd python /ctf/ctfd-platform/scripts/import_curated.py
   ```

6. Set `CURATED_OSINT_PHONE` to the verified international branch digits in the
   organizer's private deployment environment. Then stage the pack:

   ```sh
   docker compose exec -e CURATED_OSINT_PHONE ctfd python /ctf/ctfd-platform/scripts/import_curated.py --apply
   ```

   The script adopts the already hidden OSINT draft only if its category and
   shared-handout marker match. It rejects unmanaged name conflicts, a changed
   OSINT answer, pack participant activity or a started pack round. Rerunning
   before participant activity does not duplicate challenges, hints or files.
   If the file upload fails, the pack remains hidden; rerun staging to retry it.

7. In Rounds admin, verify the pending `Students - Wednesday` round is 180
   minutes, with five initial challenges. End the legacy active round before
   starting the new one. No legacy round is ended automatically by this pack.
8. During the explicitly requested rehearsal, test two actual participant teams:
   launch/download, solve, wrong flag, another team's flag, expiry and score.
   Check a real Whale launch and routing for every app. Do not infer production
   readiness from local HTTP tests or the configured 100-container setting.

Whale currently allows one running live challenge per team. Launching another
replaces the previous container and can change its flag. Submit the solved live
challenge before switching. These apps deliberately keep no required persistent
progress.

## OSINT organizer evidence

The note's coordinates come from the Google Maps link on the business's own
location page. The matching branch is the pizza takeaway in Portree on the
Isle of Skye. The location page is the authority for the branch number; the
site-wide footer belongs to a different/older location. The answer itself is
kept out of this tracked guide and the player attachment.

Recheck the public sources shortly before the event. No call or message to the
business is needed. Keep a private evidence copy for adjudicating changed map
listings. The existing four-character team tokens and flag-sharing alerts are
unchanged by this pack; they discourage copied flags but cannot prevent teams
sharing methods or manually reconstructing an answer.

## Operational limits

The web apps contain deliberate SQL injection, missing ownership checks and
template interpretation. Deploy them only as isolated challenge containers,
without the Docker socket, host filesystem mounts or CTFd secrets. The template
puzzle exposes a dummy configuration through a Jinja sandbox; its intended solve
does not require OS command execution. The actual node network isolation must
be verified during deployment.

Ending or hiding a challenge stops new scoring through round controls; it does
not erase downloaded files or guarantee that already running containers stop.
Manage those containers through Whale separately.
