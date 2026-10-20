"""예약 시각이 지난 릴스를 인스타그램에 올린다. (GitHub Actions에서 실행)

    python publish.py                  # 예약 시각 지난 것 1개 게시
    python publish.py --dry-run        # 무엇이 올라갈지 보기만
    python publish.py --check <폴더>   # 인스타가 영상을 받아 가는지만 시험 (게시 안 함)
    python publish.py --now <폴더>     # 예약 시각 무시하고 지금 게시

필요한 시크릿: IG_FACELESS_TOKEN, IG_FACELESS_USER_ID
영상·표지 주소: GitHub Pages(있으면) → raw.githubusercontent 순서로 시도
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parent
QUEUE, DONE = ROOT / "queue", ROOT / "done"
KST = timezone(timedelta(hours=9))
GRAPH = "https://graph.instagram.com/v25.0"


def env(*names):
    for n in names:
        if os.environ.get(n):
            return os.environ[n]
    return None


def media_bases() -> list[str]:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    ref = os.environ.get("GITHUB_SHA") or "main"
    bases = []
    if os.environ.get("MEDIA_BASE"):
        bases.append(os.environ["MEDIA_BASE"].rstrip("/"))
    if repo:
        owner, name = repo.split("/")
        bases.append(f"https://{owner.lower()}.github.io/{name}")
        bases.append(f"https://raw.githubusercontent.com/{repo}/{ref}")
    return bases


def url_ok(u: str) -> bool:
    try:
        r = requests.head(u, timeout=20, allow_redirects=True)
        return r.status_code == 200
    except requests.RequestException:
        return False


def api(method, path, token, **params):
    params["access_token"] = token
    r = requests.request(method, f"{GRAPH}/{path}", timeout=60,
                         data=params if method == "POST" else None,
                         params=params if method == "GET" else None)
    try:
        body = r.json()
    except ValueError:
        body = {"raw": r.text}
    if r.status_code >= 400 or "error" in body:
        raise RuntimeError(f"{method} {path} 실패: {body}")
    return body


def wait(cid, token, tries=60):
    """컨테이너 처리 대기 (최대 약 10분). 반환: (성공여부, 상태설명)"""
    for _ in range(tries):
        st = api("GET", cid, token, fields="status_code,status")
        code = st.get("status_code")
        if code == "FINISHED":
            return True, "FINISHED"
        if code in ("ERROR", "EXPIRED"):
            return False, f"{code}: {st.get('status')}"
        time.sleep(10)
    return False, "시간 초과"


def caption_of(post) -> str:
    tags = " ".join("#" + t.lstrip("#").replace(" ", "") for t in post.get("hashtags", [])[:5])
    cap = post.get("caption", "").strip()
    return f"{cap}\n\n{tags}".strip() if tags else cap


def make_container(d: Path, post: dict, uid: str, token: str):
    rel = quote(d.relative_to(ROOT).as_posix())
    errors = []
    for base in media_bases():
        video, cover = f"{base}/{rel}/reel.mp4", f"{base}/{rel}/cover.jpg"
        if not url_ok(video):
            errors.append(f"{base}: 영상 주소가 아직 안 열림")
            continue
        params = dict(media_type="REELS", video_url=video, caption=caption_of(post), share_to_feed="true")
        if url_ok(cover):
            params["cover_url"] = cover
        print(f"  영상 주소: {video}")
        cid = api("POST", f"{uid}/media", token, **params)["id"]
        ok, why = wait(cid, token)
        if ok:
            return cid
        errors.append(f"{base}: {why}")
        print(f"  ✗ {why} → 다른 주소로 다시 시도")
    raise RuntimeError("영상 처리 실패: " + " / ".join(errors))


def due_posts(now):
    for p in sorted(QUEUE.glob("*/post.json")):
        post = json.loads(p.read_text(encoding="utf-8"))
        if datetime.fromisoformat(post["scheduled_at"]) <= now:
            yield p.parent, post


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check")
    ap.add_argument("--now")
    a = ap.parse_args()
    now = datetime.now(KST)

    if a.check or a.now:
        name = a.check or a.now
        d = QUEUE / name
        if not (d / "post.json").exists():
            sys.exit(f"queue/{name} 가 없어요")
        targets = [(d, json.loads((d / "post.json").read_text(encoding="utf-8")))]
    else:
        targets = list(due_posts(now))[:1]  # 한 번에 1개만 (밀린 게 있으면 다음 시간에)

    if not targets:
        print("지금 올릴 게시물이 없어요.")
        return
    uid, token = env("IG_USER_ID", "IG_FACELESS_USER_ID"), env("IG_TOKEN", "IG_FACELESS_TOKEN")
    for d, post in targets:
        print(f"→ {post['ep']}화 {post['topic']} ({post['scheduled_at'][:16]})")
        if not post.get("caption", "").strip():
            sys.exit("  ✗ 캡션이 비어 있어서 올리지 않아요. post.json의 caption을 채워 주세요.")
        if a.dry_run:
            print(f"  [dry-run] 주소 후보: {media_bases()}\n  캡션 {len(caption_of(post))}자")
            continue
        if not uid or not token:
            sys.exit("  ✗ IG_FACELESS_USER_ID / IG_FACELESS_TOKEN 시크릿이 없어요.")
        cid = make_container(d, post, uid, token)
        if a.check:
            print("  ✓ 시험 통과: 인스타가 영상을 정상으로 받아 갔어요 (게시는 안 함)")
            continue
        mid = api("POST", f"{uid}/media_publish", token, creation_id=cid)["id"]
        try:
            link = api("GET", mid, token, fields="permalink").get("permalink", "")
        except Exception:
            link = ""
        post["published"] = {"at": now.isoformat(), "media_id": mid, "link": link}
        (d / "post.json").write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")
        DONE.mkdir(exist_ok=True)
        dst = DONE / d.name
        shutil.move(str(d), str(dst))
        (dst / "reel.mp4").unlink(missing_ok=True)  # 저장소 용량 절약 (원본은 내 컴퓨터 점토\영상에 있음)
        print(f"  ✓ 게시 완료 {link}")


if __name__ == "__main__":
    main()
