"""Publication slots for the next batch, so a late or repeated routine never overlaps or schedules in the past."""
import json
import sys
from datetime import datetime, time, timedelta

from shared.post_queue import load_queue
from shared.timeutil import now_local, parse_time

REEL_HOUR = 12
CAROUSEL_HOUR = 19
CAROUSEL_DAY_OFFSETS = (1, 3, 5)
DAYS = 7
SKIP_IF_QUEUED_AHEAD = timedelta(days=2)


def next_slots(queue: list[dict], now: datetime) -> dict:
    last = max((parse_time(entry["scheduled_at"]) for entry in queue), default=None)
    if last is not None and last - now > SKIP_IF_QUEUED_AHEAD:
        return {"skip": True, "reason": f"queue already scheduled until {last.isoformat()}"}
    start_after = max(now, last) if last is not None else now
    first_day = start_after.date()
    if datetime.combine(first_day, time(REEL_HOUR), tzinfo=now.tzinfo) <= start_after:
        first_day += timedelta(days=1)
    days = [first_day + timedelta(days=offset) for offset in range(DAYS)]

    def at(day, hour):
        return datetime.combine(day, time(hour), tzinfo=now.tzinfo).isoformat()

    return {"skip": False, "batch": first_day.isoformat(),
            "reels": [at(day, REEL_HOUR) for day in days],
            "carousels": [at(days[offset], CAROUSEL_HOUR) for offset in CAROUSEL_DAY_OFFSETS]}


def main() -> int:
    print(json.dumps(next_slots(load_queue(), now_local()), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
