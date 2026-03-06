from __future__ import annotations
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint

console = Console()


def make_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )


def print_results(jobs: list[dict], quiet: bool = False) -> None:
    if not jobs:
        if not quiet:
            console.print("[yellow]No new jobs found.[/yellow]")
        return

    table = Table(title=f"New Jobs Found: {len(jobs)}", show_lines=True)
    table.add_column("Company", style="bold green", min_width=15)
    table.add_column("Role", min_width=25)
    table.add_column("Location", min_width=15)
    table.add_column("Source", style="dim", min_width=20)
    table.add_column("Link", style="blue")

    for j in jobs:
        url_display = j.get("url", "")[:50] or "N/A"
        table.add_row(
            j.get("company", ""),
            j.get("role", ""),
            j.get("location", ""),
            j.get("source_repo", ""),
            url_display,
        )
    console.print(table)


def print_summary(new: int, excluded: int, repos_checked: int) -> None:
    console.print(
        f"\n[bold]Summary:[/bold] "
        f"[green]{new} new[/green] | "
        f"[red]{excluded} excluded[/red] | "
        f"[dim]{repos_checked} repos checked[/dim]"
    )


def print_history(entries: list[str]) -> None:
    for line in entries:
        console.print(line)


def print_repos(repos: list[dict]) -> None:
    table = Table(title="Monitored Repos")
    table.add_column("Repo", style="bold")
    table.add_column("File")
    for r in repos:
        table.add_row(r["owner_repo"], r["file_path"])
    console.print(table)
