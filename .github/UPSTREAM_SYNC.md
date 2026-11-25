# Automatic Instagram Agent updates

The workflow runs daily at 03:17 UTC / 06:17 Europe/Istanbul.

It fetches upstream, merges changes into an isolated branch, increments the plugin version, opens a PR and merges it. Claude automatic sync consumes the merged version-bumping PR. Direct pushes alone did not synchronize during our test. PR #1 (merge a31b880) synchronized without manual update.

The workflow uses the repository GITHUB_TOKEN with contents and pull-requests write permissions. Repository Actions settings must allow GitHub Actions to create pull requests. No personal access token is needed.

Unexpected merge conflicts stop the run. Only plugin manifest conflicts from local version increments are resolved using upstream metadata, followed by a new local version. A monthly release keeps the public fork active. Unchanged daily checks do not create releases.

Manual test: Actions → Sync Instagram Agent upstream → Run workflow → enable force_release. This tests the same automated PR and Claude synchronization path. A workflow success verifies GitHub release delivery; verify the merge SHA in Claude to confirm the receiving side.

Source: https://support.claude.com/en/articles/13837433-manage-plugins-for-your-organization
