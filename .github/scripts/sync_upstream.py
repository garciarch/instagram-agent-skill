#!/usr/bin/env python3
"""Merge upstream and release through a version-bumping PR for Claude."""
import datetime
import json
import os
from pathlib import Path
import re
import subprocess

REPO = os.environ["GH_REPO"]
UPSTREAM = "https://github.com/Jakeschincariol/instagram-agent-skill.git"
MANIFEST = ".claude-plugin/plugin.json"
MARKETPLACE = ".claude-plugin/marketplace.json"

def run(*args, check=True):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)

def git(*args, check=True):
    return run("git", *args, check=check).stdout.strip()

def api(path, method="GET", payload=None):
    args = ["gh", "api", "--method", method, path]
    result = subprocess.run(args + (["--input", "-"] if payload is not None else []),
                            input=json.dumps(payload) if payload is not None else None,
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout) if result.stdout.strip() else {}

def version_tuple(value):
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError("Expected numeric semantic version, got " + value)
    return tuple(map(int, match.groups()))

git("config", "user.name", "github-actions[bot]")
git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
git("fetch", "origin", "main")
git("checkout", "-B", "main", "origin/main")
git("fetch", UPSTREAM, "main")
upstream = git("rev-parse", "FETCH_HEAD")
base = git("rev-parse", "HEAD")
old_version = json.loads(Path(MANIFEST).read_text())["version"]
health_path = Path(".github/upstream-sync-health.json")
now = datetime.datetime.now(datetime.timezone.utc)
health = json.loads(health_path.read_text()) if health_path.exists() else {}
last = health.get("last_successful_check")
health_due = not last or (now - datetime.datetime.fromisoformat(last)).days >= 28
has_update = run("git", "merge-base", "--is-ancestor", upstream, base, check=False).returncode != 0
force = os.environ.get("FORCE_RELEASE", "false") == "true"
if not has_update and not health_due and not force:
    print("No upstream update; scheduled check succeeded.")
    raise SystemExit(0)

branch = "automation/instagram-sync-" + os.environ["GITHUB_RUN_ID"] + "-" + os.environ.get("GITHUB_RUN_ATTEMPT", "1")
git("checkout", "-b", branch)
if has_update:
    merged = run("git", "merge", "--no-commit", "--no-ff", upstream, check=False)
    if merged.returncode:
        conflicts = git("diff", "--name-only", "--diff-filter=U").splitlines()
        # Only our release metadata is allowed to conflict. All other conflicts stop the run.
        if not conflicts or set(conflicts) - {MANIFEST, MARKETPLACE}:
            raise RuntimeError("Upstream merge requires review: " + ", ".join(conflicts))
        for path in conflicts:
            git("checkout", "--theirs", "--", path)
            git("add", path)

manifest = json.loads(Path(MANIFEST).read_text())
current = max(version_tuple(old_version), version_tuple(manifest["version"]))
new_version = f"{current[0]}.{current[1]}.{current[2] + 1}"
manifest["version"] = new_version
Path(MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n")
marketplace = json.loads(Path(MARKETPLACE).read_text())
for plugin in marketplace["plugins"]:
    if plugin["name"] == manifest["name"]:
        plugin["version"] = new_version
Path(MARKETPLACE).write_text(json.dumps(marketplace, indent=2) + "\n")
health_path.write_text(json.dumps({
    "upstream": "Jakeschincariol/instagram-agent-skill",
    "upstream_sha": upstream,
    "last_successful_check": now.isoformat(),
    "release_version": new_version,
    "purpose": "Monthly release keeps the public fork schedule active."
}, indent=2) + "\n")
git("add", MANIFEST, MARKETPLACE, str(health_path))
git("commit", "-m", "chore: release Instagram Agent " + new_version)
head = git("rev-parse", "HEAD")
git("push", "origin", "HEAD:refs/heads/" + branch)
pr = api(f"repos/{REPO}/pulls", "POST", {
    "head": branch, "base": "main",
    "title": "chore: sync and release Instagram Agent " + new_version,
    "body": "Automated upstream synchronization and version bump for Claude auto-sync.\n\nUpstream: " + upstream + "\nValidation: parsed both plugin manifests; non-metadata merge conflicts fail closed."
})
result = api(f"repos/{REPO}/pulls/{pr['number']}/merge", "PUT",
             {"sha": head, "merge_method": "merge"})
if not result.get("merged"):
    raise RuntimeError("Release PR was not merged: " + json.dumps(result))
print("Released", new_version, "via", pr["html_url"], "merge", result["sha"])
