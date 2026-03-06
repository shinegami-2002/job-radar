from __future__ import annotations
import logging
import os
import time
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

MAX_FIELDS_PER_EMBED = 20


def _get_webhook_url() -> str:
    url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not url:
        raise EnvironmentError(
            "DISCORD_WEBHOOK_URL is not set. "
            "Add it to your .env file or set it as an environment variable."
        )
    return url


def _build_embed(jobs: list[dict], batch: int, total_batches: int, total_count: int) -> dict:
    now = datetime.now(timezone.utc)
    if total_batches > 1:
        title = f"Job Radar -- Batch {batch}/{total_batches} ({total_count} total)"
    else:
        title = f"Job Radar -- {total_count} New Role{'s' if total_count != 1 else ''} Found"

    repo_count = len({j["source_repo"] for j in jobs})
    description = f"Found {total_count} new role{'s' if total_count != 1 else ''} across {repo_count} repo{'s' if repo_count != 1 else ''}"

    fields = []
    for j in jobs:
        location = j.get("location") or "Unknown"
        url = j.get("url", "")
        source = j.get("source_repo", "")
        apply_text = f"[Apply Here]({url})" if url else "No link"
        fields.append({
            "name": f"{j['company']} -- {j['role']}"[:256],
            "value": f"{location}\n{apply_text}\nSource: {source}"[:1024],
            "inline": False,
        })

    return {
        "title": title[:256],
        "description": description[:4096],
        "color": 5763719,
        "fields": fields,
        "footer": {"text": f"Job Radar - {now.strftime('%Y-%m-%d %H:%M')} UTC"},
        "timestamp": now.isoformat(),
    }


def send_jobs(jobs: list[dict]) -> bool:
    """Send jobs to Discord. Splits into batches. Returns True if all sent ok."""
    if not jobs:
        return True
    url = _get_webhook_url()
    batches = [jobs[i : i + MAX_FIELDS_PER_EMBED] for i in range(0, len(jobs), MAX_FIELDS_PER_EMBED)]
    total_batches = len(batches)
    all_ok = True
    for i, batch in enumerate(batches, 1):
        embed = _build_embed(batch, i, total_batches, len(jobs))
        payload = {"embeds": [embed]}
        ok = _post_with_retry(url, payload)
        if not ok:
            all_ok = False
    return all_ok


def _post_with_retry(url: str, payload: dict, retries: int = 2) -> bool:
    for attempt in range(retries + 1):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code in (200, 204):
                return True
            logger.error("Discord webhook returned %d: %s", resp.status_code, resp.text[:200])
        except requests.RequestException as exc:
            logger.error("Discord webhook error (attempt %d): %s", attempt + 1, exc)
        if attempt < retries:
            time.sleep(5)
    return False


def send_test_message(webhook_url: str | None = None) -> bool:
    url = webhook_url or _get_webhook_url()
    now = datetime.now(timezone.utc)
    payload = {
        "embeds": [{
            "title": "Job Radar -- Test Message",
            "description": "Webhook is connected and working.",
            "color": 5763719,
            "footer": {"text": f"Job Radar - {now.strftime('%Y-%m-%d %H:%M')} UTC"},
        }]
    }
    return _post_with_retry(url, payload)
