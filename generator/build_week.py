"""Render, validate and queue a batch: `python -m generator.build_week content/weeks/<batch>.json`."""
import argparse
import sys
from pathlib import Path

from generator.batch import load_batch, quote_ids_of
from generator.history import HISTORY_PATH, load_history, recent_footage, record_use, save_history
from generator.quotes import QUOTES_PATH, load_quotes
from generator.render_carousel import render_carousel
from generator.render_reel import render_reel
from generator.validate import check_media, check_plan
from shared.config import OUTPUT_DIR, Settings, load_settings, require
from shared.post_queue import QUEUE_PATH, add_entries, load_queue, make_entry, save_queue
from shared.timeutil import now_local, parse_time


def render_item(item, quotes, settings: Settings, output_dir, exclude_footage, *,
                reel_renderer, carousel_renderer) -> tuple[list[str], str | None]:
    """Render one item into output_dir/<id>/; returns (media file names, footage id or None)."""
    item_dir = Path(output_dir) / item["id"]
    if item["type"] == "reel":
        footage_id = reel_renderer(item, quotes[item["quote_id"]], item_dir / "work", item_dir / "reel.mp4",
                                   api_key=require(settings.pexels_api_key, "PEXELS_API_KEY"),
                                   exclude_footage=exclude_footage)
        return ["reel.mp4"], footage_id
    paths = carousel_renderer(item, quotes, item_dir, settings.handle)
    return [path.name for path in paths], None


def build_week(batch_path, *, now, settings, quotes_path=QUOTES_PATH, queue_path=QUEUE_PATH,
               history_path=HISTORY_PATH, output_dir=OUTPUT_DIR, reel_renderer=render_reel,
               carousel_renderer=render_carousel, media_checker=check_media) -> list[str]:
    """Render and validate a batch; queue and history are written only when there are no errors."""
    batch = load_batch(batch_path)
    quotes = load_quotes(quotes_path)
    history = load_history(history_path)
    errors = check_plan(batch, quotes, history, now)
    if errors:
        return errors
    exclude = recent_footage(history, now.date())
    entries, footage_by_item = [], {}
    for item in batch["items"]:
        try:
            media, footage_id = render_item(item, quotes, settings, output_dir, exclude,
                                            reel_renderer=reel_renderer, carousel_renderer=carousel_renderer)
        except Exception as exc:  # keep going so one run reports every broken item
            errors.append(f"{item['id']}: render failed: {exc}")
            continue
        if footage_id and footage_id != "fallback":
            exclude.add(footage_id)
            footage_by_item[item["id"]] = footage_id
        entries.append(make_entry(item, media))
    if errors:
        return errors
    errors = media_checker(batch, output_dir)
    if errors:
        return errors
    try:
        queue = add_entries(load_queue(queue_path), entries)
    except ValueError as exc:
        return [str(exc)]
    for item in batch["items"]:
        footage = [footage_by_item[item["id"]]] if item["id"] in footage_by_item else []
        record_use(history, item_id=item["id"], quote_ids=quote_ids_of(item), footage_ids=footage,
                   on=parse_time(item["scheduled_at"]).date())
    save_queue(queue_path, queue)
    save_history(history_path, history)
    return []


def preview_item(batch_path, item_id, *, settings, quotes_path=QUOTES_PATH, queue_path=QUEUE_PATH,
                 output_dir=OUTPUT_DIR, enqueue=False, reel_renderer=render_reel,
                 carousel_renderer=render_carousel, media_checker=check_media) -> list[str]:
    """Render a single item for review (no batch-size rules); optionally queue it."""
    batch = load_batch(batch_path)
    item = next((candidate for candidate in batch["items"] if candidate["id"] == item_id), None)
    if item is None:
        return [f"{item_id}: not found in {batch_path}"]
    quotes = load_quotes(quotes_path)
    missing = [quote_id for quote_id in quote_ids_of(item) if quote_id not in quotes]
    if missing:
        return [f"{item_id}: quotes not in bank: {missing}"]
    media, _ = render_item(item, quotes, settings, output_dir, set(),
                           reel_renderer=reel_renderer, carousel_renderer=carousel_renderer)
    errors = media_checker({"week": batch["week"], "items": [item]}, output_dir)
    if errors:
        return errors
    if enqueue:
        save_queue(queue_path, add_entries(load_queue(queue_path), [make_entry(item, media)]))
    return []


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render, validate and queue a content batch")
    parser.add_argument("batch", type=Path)
    parser.add_argument("--preview", metavar="ITEM_ID", help="render only this item, skipping batch rules")
    parser.add_argument("--enqueue", action="store_true", help="with --preview: add the item to queue.json")
    args = parser.parse_args(argv)
    settings = load_settings()
    try:
        if args.preview:
            errors = preview_item(args.batch, args.preview, settings=settings, enqueue=args.enqueue)
        else:
            errors = build_week(args.batch, now=now_local(), settings=settings)
    except Exception as exc:  # report any failure as a readable line for the routine
        errors = [f"{type(exc).__name__}: {exc}"]
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if not errors:
        print("OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
