# Job Radar

A Python CLI that monitors curated GitHub repositories for new grad SWE, AI, and ML job postings and sends rich Discord notifications when new listings appear. It watches 6+ repos out of the box, filters jobs by configurable keywords, deduplicates across sources, and delivers formatted Discord embeds straight to your server. Runs locally with a single command or completely free on GitHub Actions (every 2 hours, 12 times daily).

## Quick Start

```bash
# 1. Clone
git clone https://github.com/shinegami-2002/job-radar.git
cd job-radar

# 2. Install
python -m venv .venv && source .venv/bin/activate && pip install -e .

# 3. Set up .env
cp .env.example .env
# Edit .env and paste your Discord webhook URL (see setup below)

# 4. Test your webhook
job-radar test-webhook

# 5. First run
job-radar check --notify
```

The first run records a baseline for each repo -- no notifications are sent. Starting from the second run, you will get Discord alerts for any new postings.

## Discord Webhook Setup

1. Open Discord and go to your server.
2. Right-click the channel you want notifications in, then click **Edit Channel**.
3. Go to **Integrations** and then **Webhooks**.
4. Click **New Webhook** and name it `Job Radar`.
5. Click **Copy Webhook URL**.
6. Paste it into your `.env` file:
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
   ```

## CLI Commands

| Command | Description |
|---------|-------------|
| `job-radar check` | Check all repos, print results |
| `job-radar check --notify` | Check and send Discord notification |
| `job-radar check --quiet` | Minimal output (for cron/CI) |
| `job-radar check --dry-run` | Show what would be sent without sending |
| `job-radar history` | Show all findings |
| `job-radar history --today` | Today's findings only |
| `job-radar history --week` | Past 7 days |
| `job-radar repos` | List monitored repos |
| `job-radar repos add owner/repo file.md` | Add a repo |
| `job-radar repos remove owner/repo` | Remove a repo |
| `job-radar test-webhook` | Send a test Discord message |
| `job-radar reset` | Clear state for a fresh start |

## GitHub Actions Setup (Free, Automated)

Run job-radar in the cloud with zero infrastructure cost:

1. **Fork** this repo on GitHub.
2. Go to **Settings > Secrets and variables > Actions**.
3. Click **New repository secret** and add:
   - Name: `DISCORD_WEBHOOK_URL`
   - Value: your webhook URL
4. (Optional) Add `GITHUB_TOKEN` as another secret to avoid API rate limits.
5. Go to the **Actions** tab and enable workflows.
6. The workflow runs automatically every 2 hours (12 times daily).
7. To trigger manually: **Actions > Job Radar > Run workflow**.

State is cached between runs so deduplication and baseline tracking persist across workflow executions.

## Adding and Removing Repos

Use the CLI:

```bash
# Add a new repo to monitor
job-radar repos add cvrve/New-Grad-2026 README.md

# Remove a repo
job-radar repos remove cvrve/New-Grad-2026

# See what's being watched
job-radar repos
```

You can also edit `~/.job-radar/config.json` directly. Each repo entry looks like:

```json
{
  "owner_repo": "SimplifyJobs/New-Grad-Positions",
  "file_path": "README.md"
}
```

## Customizing Keywords

Edit `~/.job-radar/config.json` to change which jobs get through the filter:

```json
{
  "repos": [ ... ],
  "include_keywords": [
    "software engineer", "swe", "ai engineer", "ml engineer",
    "machine learning", "data engineer", "full stack", "backend",
    "new grad", "junior", "entry level"
  ],
  "exclude_keywords": [
    "phd required", "security clearance", "no sponsorship",
    "senior staff", "principal", "10+ years"
  ]
}
```

A job must match at least one include keyword and zero exclude keywords to pass the filter.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| First run shows no notifications | Normal. The first run records baseline SHAs only. You will get alerts starting from the second run. |
| Discord messages not arriving | Run `job-radar test-webhook` to verify your webhook URL is correct. |
| GitHub API rate limit errors | Add a `GITHUB_TOKEN` to your `.env` file. A personal access token (no scopes needed) gets you 5,000 requests/hour instead of 60. |
| Malformed rows in job listings | Warnings are logged but the tool does not crash. Unparseable rows are skipped. |
| Jobs failed to send to Discord | They are saved to `~/.job-radar/unsent.json` and retried automatically on the next run. |

## Built With

- **Python** -- core language
- **click** -- CLI framework
- **rich** -- terminal formatting and progress bars
- **requests** -- HTTP client for GitHub API and Discord webhooks
- **GitHub Actions** -- free scheduled automation
