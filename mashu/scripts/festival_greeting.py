#!/usr/bin/env python3
"""Return a once-per-day light festival greeting for Mashu mode."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".state"
STATE_FILE = STATE_DIR / "festival_seen.json"


@dataclass(frozen=True)
class Festival:
    name: str
    greeting: str
    tone: str = "joy"


FIXED_FESTIVALS: dict[tuple[int, int], Festival] = {
    (1, 1): Festival("元旦", "新年第一天，麻薯君祝你今天轻轻松松，开一个软乎乎的好头。"),
    (2, 14): Festival("情人节", "今天是情人节，麻薯君送你一点甜甜的心意，愿你被喜欢和温柔包住。"),
    (3, 8): Festival("妇女节", "今天是妇女节，麻薯君祝你被尊重、被看见，也有一小块完全属于自己的快乐。"),
    (4, 1): Festival("愚人节", "今天是愚人节，麻薯君允许你偷偷调皮一下，但只调皮一点点。"),
    (5, 1): Festival("劳动节", "劳动节快乐。今天适合把自己从忙碌里捞出来，认真休息一会儿。"),
    (5, 4): Festival("青年节", "青年节快乐。愿你今天还有一点热乎乎的好奇心，和一点不服输的小劲儿。"),
    (6, 1): Festival("儿童节", "儿童节快乐。今天麻薯君批准你幼稚一点、快乐一点、想吃什么就认真惦记一下。"),
    (7, 7): Festival("世界巧克力日", "今天是世界巧克力日，麻薯君祝你获得一点甜味补给，心情也跟着融化一点。"),
    (8, 8): Festival("国际猫咪日", "今天是国际猫咪日，麻薯君祝你像猫一样理直气壮地舒服一下。"),
    (9, 10): Festival("教师节", "教师节快乐。今天适合感谢那些点亮过你的人，也轻轻谢谢努力学习的自己。"),
    (10, 1): Festival("国庆节", "国庆节快乐。今天适合放松、吃点好的，也把心情晾到阳光里。"),
    (10, 31): Festival("万圣夜", "今天是万圣夜，麻薯君祝你获得一点可爱的怪诞快乐。"),
    (11, 11): Festival("双十一", "今天是双十一，麻薯君提醒你买得开心，也要守住钱包的小被子。"),
    (12, 24): Festival("平安夜", "平安夜快乐。麻薯君祝你今晚平平安安，心里有一点暖光。"),
    (12, 25): Festival("圣诞节", "圣诞快乐。麻薯君送你一小份冬天的亮晶晶和热乎乎。"),
    (12, 31): Festival("跨年夜", "跨年夜快乐。麻薯君陪你把这一年慢慢收好，再轻轻走向下一年。"),
}


def nth_weekday(year: int, month: int, weekday: int, nth: int) -> date:
    """Return the nth weekday in a month. Monday is 0."""
    current = date(year, month, 1)
    offset = (weekday - current.weekday()) % 7
    return date(year, month, 1 + offset + (nth - 1) * 7)


def movable_festival(day: date) -> Festival | None:
    if day == nth_weekday(day.year, 5, 6, 2):
        return Festival("母亲节", "母亲节快乐。麻薯君祝今天的爱意都能被好好接住，也被温柔回应。")
    if day == nth_weekday(day.year, 6, 6, 3):
        return Festival("父亲节", "父亲节快乐。麻薯君祝今天的感谢不用太用力，也能稳稳送到。")
    if day == nth_weekday(day.year, 11, 3, 4):
        return Festival("感恩节", "感恩节快乐。麻薯君祝你今天刚好想起一些值得感谢的小事。")
    return None


def festival_for(day: date) -> Festival | None:
    return movable_festival(day) or FIXED_FESTIVALS.get((day.month, day.day))


def load_seen() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_seen(seen: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Return a once-per-day Mashu festival greeting.")
    parser.add_argument("--date", help="Override date as YYYY-MM-DD for tests.")
    parser.add_argument("--timezone", default="Asia/Shanghai", help="IANA timezone name.")
    parser.add_argument("--mark", action="store_true", help="Record that today's greeting was checked.")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    if args.date:
        today = date.fromisoformat(args.date)
    else:
        today = datetime.now(ZoneInfo(args.timezone)).date()

    key = today.isoformat()
    seen = load_seen()
    already_seen = seen.get("last_greeted_date") == key
    festival = festival_for(today)
    should_greet = festival is not None and not already_seen

    if args.mark:
        seen["last_checked_date"] = key
        if should_greet:
            seen["last_greeted_date"] = key
            seen["last_festival"] = festival.name
        save_seen(seen)

    payload = {
        "date": key,
        "should_greet": should_greet,
        "already_seen": already_seen,
        "festival": festival.name if festival else None,
        "tone": festival.tone if festival else None,
        "greeting": festival.greeting if should_greet else None,
    }

    if args.format == "text":
        print(payload["greeting"] or "")
        return
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
