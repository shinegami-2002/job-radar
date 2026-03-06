from __future__ import annotations
import logging
import sys
from datetime import date, timedelta

import click
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def _setup_logging(quiet: bool) -> None:
    level = logging.ERROR if quiet else logging.INFO
    logging.getLogger("job_radar").setLevel(level)


@click.group()
def cli() -> None:
    """Job Radar -- monitor GitHub repos for new grad job postings."""


@cli.command()
@click.option("--notify", is_flag=True, help="Send Discord notification for new jobs.")
@click.option("--quiet", is_flag=True, help="Minimal terminal output.")
@click.option("--dry-run", is_flag=True, help="Show what would be sent without sending.")
def check(notify: bool, quiet: bool, dry_run: bool) -> None:
    """Check all repos for new job listings."""
    from job_radar.config import load_config
    from job_radar.state import (
        get_sha, set_sha, is_seen_job, add_seen_job,
        prune_seen_jobs, append_findings, load_unsent, save_unsent,
    )
    from job_radar.github_api import get_latest_sha, get_diff, get_raw_file
    from job_radar.parser import parse_diff, parse_raw_file
    from job_radar.filters import filter_jobs
    from job_radar.dedup import dedup_jobs, filter_seen, make_dedup_key
    from job_radar.discord import send_jobs
    from job_radar.display import make_progress, print_results, print_summary

    _setup_logging(quiet)
    logger = logging.getLogger("job_radar")

    cfg = load_config()
    repos = cfg["repos"]
    include_kw = cfg["include_keywords"]
    exclude_kw = cfg["exclude_keywords"]

    today = str(date.today())
    prune_seen_jobs(days=30)

    # Retry any unsent jobs first
    unsent = load_unsent()
    if unsent and notify and not dry_run:
        if not quiet:
            click.echo(f"Retrying {len(unsent)} previously unsent jobs...")
        ok = send_jobs(unsent)
        if ok:
            save_unsent([])

    all_new_jobs: list[dict] = []
    first_run_repos: list[str] = []
    repos_checked = 0
    excluded_count = 0

    with make_progress() as progress:
        task = progress.add_task("Checking repos...", total=len(repos))

        for repo_cfg in repos:
            owner_repo = repo_cfg["owner_repo"]
            file_path = repo_cfg["file_path"]
            progress.update(task, description=f"Checking {owner_repo}...")

            try:
                new_sha = get_latest_sha(owner_repo, file_path)
            except Exception as exc:
                logger.warning("Skipping %s: %s", owner_repo, exc)
                progress.advance(task)
                continue

            old_sha = get_sha(owner_repo, file_path)

            if old_sha is None:
                # First run: fetch full file, parse rows from last 1 day
                try:
                    raw_content = get_raw_file(owner_repo, file_path)
                    raw_jobs = parse_raw_file(raw_content, source_repo=owner_repo, max_age_days=1)
                    filtered = filter_jobs(raw_jobs, include_kw, exclude_kw)
                    excluded_count += len(raw_jobs) - len(filtered)
                    all_new_jobs.extend(filtered)
                except Exception as exc:
                    logger.warning("Could not fetch initial file for %s: %s", owner_repo, exc)
                set_sha(owner_repo, file_path, new_sha)
                first_run_repos.append(owner_repo)
                repos_checked += 1
                progress.advance(task)
                continue

            if old_sha == new_sha:
                logger.info("No changes in %s", owner_repo)
                repos_checked += 1
                progress.advance(task)
                continue

            try:
                diff_text = get_diff(owner_repo, old_sha, new_sha)
            except Exception as exc:
                logger.warning("Could not fetch diff for %s: %s", owner_repo, exc)
                progress.advance(task)
                continue

            raw_jobs = parse_diff(diff_text, source_repo=owner_repo)
            filtered = filter_jobs(raw_jobs, include_kw, exclude_kw)
            excluded_count += len(raw_jobs) - len(filtered)

            seen_keys = {make_dedup_key(j) for j in filtered if is_seen_job(make_dedup_key(j))}
            new_jobs = filter_seen(filtered, seen_keys)

            all_new_jobs.extend(new_jobs)
            set_sha(owner_repo, file_path, new_sha)
            repos_checked += 1
            progress.advance(task)

    all_new_jobs = dedup_jobs(all_new_jobs)

    if first_run_repos and not quiet:
        click.echo(
            f"\nFirst run -- baseline recorded for: {', '.join(first_run_repos)}. "
            "Showing jobs from the last 24 hours."
        )

    if not all_new_jobs:
        if not quiet:
            click.echo("No new jobs found this run.")
        print_summary(0, excluded_count, repos_checked)
        return

    for j in all_new_jobs:
        add_seen_job(make_dedup_key(j), today)

    append_findings(all_new_jobs, today)

    if dry_run:
        click.echo(f"[DRY RUN] Would send {len(all_new_jobs)} jobs to Discord.")
        print_results(all_new_jobs, quiet=quiet)
        print_summary(len(all_new_jobs), excluded_count, repos_checked)
        return

    print_results(all_new_jobs, quiet=quiet)
    print_summary(len(all_new_jobs), excluded_count, repos_checked)

    if notify:
        ok = send_jobs(all_new_jobs)
        if not ok:
            existing_unsent = load_unsent()
            save_unsent(existing_unsent + all_new_jobs)
            click.echo("Discord send failed -- jobs saved to unsent.json for next run.", err=True)
        else:
            if not quiet:
                click.echo(f"Discord notification sent for {len(all_new_jobs)} jobs.")


@cli.command()
@click.option("--today", "period", flag_value="today", help="Show only today's findings.")
@click.option("--week", "period", flag_value="week", help="Show past 7 days.")
def history(period: str | None) -> None:
    """Show recent findings from the findings log."""
    from job_radar.state import FINDINGS_FILE
    from job_radar.display import print_history

    if not FINDINGS_FILE.exists():
        click.echo("No findings yet. Run `job-radar check` first.")
        return

    lines = FINDINGS_FILE.read_text().splitlines()

    if period is None:
        print_history(lines)
        return

    today_date = date.today()
    week_start = today_date - timedelta(days=7)

    output: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith("## "):
            section_date_str = line[3:].strip()
            try:
                section_date = date.fromisoformat(section_date_str)
            except ValueError:
                in_section = False
                continue
            if period == "today":
                in_section = section_date_str == str(today_date)
            elif period == "week":
                in_section = section_date >= week_start
            else:
                in_section = False
        if in_section:
            output.append(line)

    if output:
        print_history(output)
    else:
        click.echo("No findings for the requested period.")


@cli.group(invoke_without_command=True)
@click.pass_context
def repos(ctx) -> None:
    """Manage monitored repos."""
    if ctx.invoked_subcommand is None:
        # Default: list repos
        from job_radar.config import load_config
        from job_radar.display import print_repos
        cfg = load_config()
        print_repos(cfg["repos"])


@repos.command(name="list")
def repos_list() -> None:
    """List all monitored repos."""
    from job_radar.config import load_config
    from job_radar.display import print_repos
    cfg = load_config()
    print_repos(cfg["repos"])


@repos.command(name="add")
@click.argument("owner_repo")
@click.argument("file_path")
def repos_add(owner_repo: str, file_path: str) -> None:
    """Add a repo to monitor. Example: owner/repo README.md"""
    from job_radar.config import load_config, save_config
    cfg = load_config()
    for r in cfg["repos"]:
        if r["owner_repo"] == owner_repo:
            click.echo(f"{owner_repo} is already monitored.")
            return
    cfg["repos"].append({"owner_repo": owner_repo, "file_path": file_path})
    save_config(cfg)
    click.echo(f"Added {owner_repo} ({file_path})")


@repos.command(name="remove")
@click.argument("owner_repo")
def repos_remove(owner_repo: str) -> None:
    """Remove a repo from monitoring."""
    from job_radar.config import load_config, save_config
    cfg = load_config()
    before = len(cfg["repos"])
    cfg["repos"] = [r for r in cfg["repos"] if r["owner_repo"] != owner_repo]
    if len(cfg["repos"]) == before:
        click.echo(f"{owner_repo} not found in config.")
        return
    save_config(cfg)
    click.echo(f"Removed {owner_repo}")


@cli.command("test-webhook")
def test_webhook() -> None:
    """Send a test message to the Discord webhook."""
    from job_radar.discord import send_test_message
    ok = send_test_message()
    if ok:
        click.echo("Test message sent successfully.")
    else:
        click.echo("Failed to send test message. Check DISCORD_WEBHOOK_URL.", err=True)
        sys.exit(1)


@cli.command()
@click.confirmation_option(prompt="This will clear all state. Are you sure?")
def reset() -> None:
    """Clear state.json and seen.json (fresh start)."""
    from job_radar.state import STATE_FILE, SEEN_FILE
    for f in (STATE_FILE, SEEN_FILE):
        if f.exists():
            f.unlink()
            click.echo(f"Deleted {f}")
    click.echo("State reset. Next run will record baseline SHAs.")
