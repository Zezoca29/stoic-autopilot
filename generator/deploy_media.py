"""Publish pending media to the gh-pages branch: `python -m generator.deploy_media`."""
import shutil
import subprocess
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

from shared.config import OUTPUT_DIR, ROOT
from shared.post_queue import QUEUE_PATH, has_pending, load_queue
from shared.timeutil import now_local, parse_time

SITE_DIR = ROOT / "site"
KEEP_DAYS = 14  # rendered files stay locally two weeks for manual TikTok uploads
BOT_IDENTITY = ["-c", "user.name=stoic-autopilot", "-c", "user.email=stoic-autopilot@users.noreply.github.com"]


def assemble(queue, output_dir, site_dir, dest) -> list[str]:
    """Copy the site plus media of entries still pending somewhere into dest; returns missing files."""
    dest = Path(dest)
    shutil.copytree(site_dir, dest, dirs_exist_ok=True)
    (dest / ".nojekyll").touch()
    missing = []
    for entry in queue:
        if not has_pending(entry):
            continue
        for name in entry["media"]:
            source = Path(output_dir) / entry["id"] / name
            if not source.exists():
                missing.append(str(source))
                continue
            target = dest / "media" / entry["id"] / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    return missing


def push_pages(dest, remote_url, run=subprocess.run) -> None:
    """Force-push dest as a one-commit gh-pages branch so the branch history never grows."""
    for cmd in (["git", "init", "-q", "-b", "gh-pages"],
                ["git", "add", "-A"],
                ["git", *BOT_IDENTITY, "commit", "-q", "-m", "deploy media"],
                ["git", "push", "-f", remote_url, "gh-pages"]):
        run(cmd, cwd=dest, check=True)


def prune_output(queue, output_dir, now, keep_days=KEEP_DAYS) -> list[str]:
    """Delete rendered folders of entries with nothing pending that are older than keep_days."""
    removed = []
    for entry in queue:
        if has_pending(entry) or now - parse_time(entry["scheduled_at"]) < timedelta(days=keep_days):
            continue
        folder = Path(output_dir) / entry["id"]
        if folder.exists():
            shutil.rmtree(folder)
            removed.append(entry["id"])
    return removed


def main() -> int:
    queue = load_queue(QUEUE_PATH)
    remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, capture_output=True,
                            text=True, check=True).stdout.strip()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        dest = Path(tmp) / "pages"
        missing = assemble(queue, OUTPUT_DIR, SITE_DIR, dest)
        if missing:
            for path in missing:
                print(f"ERROR: missing rendered file {path}", file=sys.stderr)
            return 1
        push_pages(dest, remote)
    removed = prune_output(queue, OUTPUT_DIR, now_local())
    print(f"OK: gh-pages updated; pruned {len(removed)} old output folders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
