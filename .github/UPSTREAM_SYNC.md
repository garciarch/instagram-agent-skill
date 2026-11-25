# Automatic updates

This fork follows `Jakeschincariol/instagram-agent-skill` on `main`.

- GitHub Actions runs `.github/workflows/sync-upstream.yml` daily at 03:17 UTC (06:17 Europe/Istanbul) and can also be run manually.
- The workflow uses GitHub's merge-upstream endpoint. It preserves local commits and fails on conflicts instead of force-pushing.
- Only repository contents write permission is granted to the job. No personal access token or external action is needed.
- A successful health check is recorded at most once every 28 days, keeping the public repository active so GitHub does not disable the daily schedule after 60 days of inactivity.
- Claude's marketplace source should be `garciarch/instagram-agent-skill`, with automatic synchronization enabled. Repository push events then update the installed marketplace.
- On failure, inspect the Actions run; do not report the fork as synchronized until the run succeeds.

Manual recovery: open Actions → Sync Instagram Agent upstream → Run workflow. Resolve conflicts in this fork without discarding local changes.
