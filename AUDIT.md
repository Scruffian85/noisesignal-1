# NoiseSignal audit (Oct 2026)

## What this is

A weekly cron job in a Docker container. It searches YouTube (Data API v3) for
recent music videos from small channels, scores them (`analysis.py`), adds the
top 25 to a public playlist called "Global Emerging Tracks", writes
`emerging_playlist_results.csv`, and emails a summary through Gmail SMTP.

- Entry point: cron → `scripts/run_weekly.sh` → `scheduler.py` (retries,
  timeout, email) → `main.py` (search, score, update playlist).
- State on the host: `.env`, `secret.json`, `token.pickle`, `playlist_id.txt`,
  `data/`. None of these are in git.
- One commit (Dec 2025). No CI, no deploy workflows.

The project is small, coherent and works. It's worth keeping. There's no
reason to archive it.

## Which repo is canonical

**This one (`noisesignal-1`) is canonical.** `Scruffian85/NoiseSignal`
(one commit, Aug 2025) contains only `main.py`, `config.py`,
`youtube_client.py`, `analysis.py` and `requirements.txt`. `youtube_client.py`,
`analysis.py` and `requirements.txt` are byte-identical here. `main.py` and
`config.py` here are the same code plus the logging and automation settings.
Everything else (Docker, scheduler, email, scripts) exists only here.

**Recommendation:** archive `Scruffian85/NoiseSignal` and leave a pointer to
this repo in its README. Neither repo has any committed secrets, so archiving
it is safe. Consider renaming this one to `NoiseSignal` once the old one is
archived or renamed.

## Secrets check

I checked `git log -p` on both repos for keys, tokens, passwords, Google API
keys (`AIza…`), OAuth client secrets (`GOCSPX-…`) and GitHub tokens. **I found
no committed secrets.** `.gitignore` correctly excludes `.env`, `secret.json`,
`token.pickle`, `playlist_id.txt` and `data/`. You don't need to rotate
anything because of git.

The **built Docker image** on maggie is a different matter (see S1).

## Findings, ranked by severity

Status key: **Fixed (PR)**, **Not fixed**, **Decision needed**.

### High

| # | Finding | Status |
|---|---|---|
| S1 | `Dockerfile` copied `.env` (Gmail app password), `secret.json` (OAuth client secret), `token.pickle` (YouTube refresh token) and `data/` into the image. Anyone with the image (`docker save`, a registry push, `docker history`) gets all three. It also meant a fresh clone couldn't build. | Fixed (docker-security PR). **If the image was ever pushed anywhere or copied off maggie, rotate the Gmail app password and revoke the YouTube token.** After deploying, run `docker image prune` to delete the old image layers. |
| B1 | `youtube_client.py` called `logging.basicConfig()` on import. That ran before `scheduler.py` set up logging, so the file handler was never added and `data/logs/noisesignal.log` was never written. The daily health check warns about this. | Fixed (bugfix PR) |
| B2 | If no new tracks were found (including when every search failed), `main()` returned early without rewriting the CSV. The scheduler then read **last week's** CSV and emailed it as "N New Tracks". | Fixed (bugfix PR): a CSV older than the run start is ignored. |
| B3 | With a missing or revoked token, the cron run started the browser OAuth flow (`run_local_server`) in a headless container. Each attempt hung until the 1-hour timeout, three times. | Fixed (bugfix PR): fails fast with re-auth instructions when there's no TTY. |

### Medium

| # | Finding | Status |
|---|---|---|
| R1 | The compose healthcheck called `requests.get("http://localhost:8080/health")`. Nothing listens on 8080 and `requests` isn't installed, so the container was always "unhealthy". | Fixed (docker-security PR): checks `pgrep -x cron`. |
| S2 | Port 8080 was published on all host interfaces (including the LAN and Tailscale) with nothing behind it. | Fixed (docker-security PR): removed. |
| B4 | `search_videos` swallowed every `HttpError`, including `quotaExceeded`. `main.py`'s "stop on quota" branch never ran: it kept making failing calls and then reported success. | Fixed (bugfix PR): quota errors propagate. If quota runs out before anything is found, the run fails and you get an error email. |
| B5 | `get_or_create_playlist` treated an empty `playlist_id.txt` or a deleted playlist as valid (the API returns empty `items`, not an error), so every insert failed forever. | Fixed (bugfix PR): a new playlist is created and its ID saved. |
| D1 | `requirements.txt` was completely unpinned. A rebuild could pull a new major version (pandas 3 came out after the image was likely built). | Fixed (docs-deps PR): pinned to current versions, which the tests pass against. |
| R2 | Cron jobs don't inherit the container's environment. Email only worked because `.env` was baked into the image (S1). | Fixed (docker-security PR): `.env` is bind-mounted read-only. |

### Low

| # | Finding | Status |
|---|---|---|
| S3 | YouTube titles, artist names and error text went into email HTML unescaped. Gmail strips scripts, but a crafted title could still break or spoof the layout. | Fixed (bugfix PR) |
| B6 | `PUBLISHED_AFTER` used local time but added a `Z` (UTC) suffix, so it was off by the TZ offset. | Fixed (bugfix PR) |
| R3 | No SMTP timeout: a stalled Gmail connection could hang the run. | Fixed (bugfix PR): 30s. |
| R4 | `signal.alarm` wasn't cancelled on every path. | Fixed (bugfix PR): `finally`. |
| S4 | `token.pickle` is loaded with `pickle.load`. Only a risk if someone can write that file, and then they have your token anyway. Switching to `token.json` (`Credentials.to_json`) needs a one-off migration. | Not fixed: low value. |
| R5 | A failed playlist update is logged but the run still counts as a success, so the email says tracks were added when they weren't. Making it fail would trigger retries, and each retry re-runs every search (~1,900 quota units out of 10,000 a day). | Decision needed: do you want a failed playlist update to send an error email (and maybe skip the retries)? |
| R6 | Retries re-run the whole search for errors that won't fix themselves (quota, auth). Three attempts can use most of a day's quota. | Not fixed: same trade-off as R5. |
| R7 | The daily health check result only goes to `/var/log/cron.log` inside the container. Nobody sees it. | Decision needed: email on failure? It could reuse `EmailNotifier`. |
| R8 | The container runs as root, and PID 1 is `sh -c "cron && tail -f"`, so `docker stop` waits 10s and then kills it. Harmless for a weekly job. | Not fixed |
| R9 | `docker-compose.yml` bind-mounts `./token.pickle` and `./playlist_id.txt` as files. If either is missing on the host, Docker creates a directory instead and the app breaks. | Documented in README (create them first). |
| R10 | The `noisesignal-logs` named volume is mounted over `./data/logs`, so the logs aren't in `./data/logs` on the host. Use `docker exec … tail` as the README says. | Not fixed: changing it moves your log location. |
| R11 | `emerging_playlist_results.csv` is written to `/app` (not a volume), so it's lost when the container is recreated. The health check then warns until the next Sunday. | Not fixed: moving it to `data/` changes paths in three places. Easy follow-up if you want it. |
| Q1 | `NEGATIVE_KEYWORDS` matches substrings in the description too, so "mix" rejects "remix"/"mixed" and "cover" rejects "cover art". That may be throwing away good tracks. | Decision needed (it's tuning, not a bug). |
| Q2 | The playlist is created **public**. | Decision needed, if that isn't what you want. |
| Q3 | Dead code: `Dockerfile.backup`, `scheduler.py.backup` (removed in these PRs, still in git history), plus a few unused imports and `config.PLAYLIST_TITLE` imported but unused in `scheduler.py`. `ANALYSIS.md` is an older ideas document. I left it alone. | Partly fixed (backups removed; `main.py` unused `signal` import removed) |
| Q4 | `test_email.py` isn't a real test. It writes `sample_*.html` into the repo. | Not fixed: kept as a manual preview tool; pytest now only runs `tests/`. |
| Q5 | Your email address is the hard-coded default for `NOTIFICATION_EMAIL`. It's your own repo, so that's fine, but take it out if you ever make the repo public. | Not fixed |
| D2 | The base image is `python:3.11-slim`. Google's libraries now warn that 3.11 support ends in Oct 2027. | Not fixed: bump to 3.12 or 3.13 within the next year. |

## Tests added

`tests/` (pytest) covers the scoring and filtering in `analysis.py`, quota and
auth handling in `youtube_client.py`, playlist reuse and recreation,
stale-CSV handling and retries in `scheduler.py`, and email escaping. Run it
with `pip install -r requirements.txt -r requirements-dev.txt && pytest`.

## What I couldn't verify

- `docker build`: Docker Hub is blocked from the audit sandbox. `docker compose
  config` validates and the shell scripts pass `bash -n`, but **do a
  `docker compose build && docker compose up -d` on maggie and check
  `docker ps` shows `healthy`.**
- I didn't call the real YouTube API or send real email.
