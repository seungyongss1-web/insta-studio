"""점토 폴더의 새 영상을 예약 목록(queue)에 넣는다. (내 컴퓨터에서 실행)

    python add_videos.py            # 새 영상 찾아서 예약
    python add_videos.py --list     # 예약 목록만 보기

- 영상:   ..\\영상\\<n>화_<주제>.mp4
- 썸네일: ..\\썸네일\\<n>화_썸네일.png (또는 .jpg)
- 이미 queue/ 나 done/ 에 있는 화는 건너뛴다.
- 예약 시각: config.json 의 slots(기본 13:00, 18:00) 중 비어 있는 가장 빠른 칸.
- 캡션은 비워 두고 만든다 → Claude Code가 CLAUDE.md 규칙대로 채운다.
  (캡션이 비어 있으면 publish.py가 올리지 않는다)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent
VIDEOS, THUMBS = SRC / "영상", SRC / "썸네일"
QUEUE, DONE = ROOT / "queue", ROOT / "done"
KST = timezone(timedelta(hours=9))
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def posts(folder: Path):
    for p in sorted(folder.glob("*/post.json")):
        yield p.parent, json.loads(p.read_text(encoding="utf-8"))


def taken_eps() -> set[int]:
    return {post["ep"] for d in (QUEUE, DONE) for _, post in posts(d)}


def taken_slots() -> set[str]:
    return {post["scheduled_at"] for _, post in posts(QUEUE)}


def next_slot(used: set[str]) -> datetime:
    now = datetime.now(KST) + timedelta(minutes=CFG.get("min_lead_minutes", 30))
    day = now.date()
    while True:
        for hm in CFG["slots"]:
            h, m = map(int, hm.split(":"))
            t = datetime(day.year, day.month, day.day, h, m, tzinfo=KST)
            if t > now and t.isoformat() not in used:
                return t
        day += timedelta(days=1)


def find_thumb(n: int) -> Path | None:
    for ext in (".png", ".jpg", ".jpeg"):
        p = THUMBS / f"{n}화_썸네일{ext}"
        if p.exists():
            return p
    return None


def to_jpg(src: Path, dst: Path):
    from PIL import Image
    im = Image.open(src).convert("RGB")
    im.save(dst, "JPEG", quality=90, optimize=True)


def show():
    rows = list(posts(QUEUE))
    if not rows:
        print("예약된 게시물이 없어요.")
    for d, p in rows:
        cap = p.get("caption", "").strip().splitlines()
        first = cap[0] if cap else "(캡션 비어 있음 — 채워야 올라가요)"
        print(f"  {p['scheduled_at'][:16].replace('T', ' ')}  {p['ep']}화 {p['topic']}  | {first}  [{d.name}]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        show()
        return
    if not VIDEOS.exists():
        sys.exit(f"영상 폴더가 없어요: {VIDEOS}")
    QUEUE.mkdir(exist_ok=True)
    have, used = taken_eps(), taken_slots()
    added = 0
    for v in sorted(VIDEOS.glob("*.mp4"), key=lambda p: int(re.match(r"(\d+)", p.name).group(1)) if re.match(r"\d+", p.name) else 9999):
        m = re.match(r"^(\d+)화_(.+)\.mp4$", v.name)
        if not m:
            print(f"  건너뜀(이름 형식 아님): {v.name}")
            continue
        n, topic = int(m.group(1)), m.group(2).strip()
        if n in have:
            continue
        thumb = find_thumb(n)
        if not thumb:
            print(f"  건너뜀(썸네일 없음): {n}화 {topic}")
            continue
        size_mb = v.stat().st_size / 1e6
        if size_mb > 95:
            print(f"  건너뜀(파일이 {size_mb:.0f}MB, 95MB 넘으면 GitHub에 못 올려요): {v.name}")
            continue
        t = next_slot(used)
        used.add(t.isoformat())
        d = QUEUE / f"{t:%Y-%m-%d-%H%M}-ep{n:02d}"
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy2(v, d / "reel.mp4")
        to_jpg(thumb, d / "cover.jpg")
        post = {"ep": n, "topic": topic, "scheduled_at": t.isoformat(), "caption": "", "hashtags": []}
        (d / "post.json").write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  + {n}화 {topic} → {t:%m/%d %H:%M}  [{d.name}]")
        added += 1
    print(f"새로 넣은 영상 {added}개. 지금 예약 목록:")
    show()


if __name__ == "__main__":
    main()
