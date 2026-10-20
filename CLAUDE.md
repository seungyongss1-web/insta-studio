# 점토 영상 자동 업로드 — Claude Code 작업 안내

이 폴더(점토\자동업로드)는 점토 설명 영상을 인스타그램 @mallang_knowledge 에 **매일 13:00·18:00** 자동으로 올리는 저장소다.
답변은 항상 한국어(해요체)로 한다.

## 구조
```
..\영상\<n>화_<주제>.mp4       원본 영상 (점토 폴더)
..\썸네일\<n>화_썸네일.png      원본 썸네일
add_videos.py   새 영상을 queue\<날짜-시각-epNN>\ 에 복사하고 예약 시각을 붙인다 (캡션은 비워 둠)
publish.py      GitHub Actions가 매시 7분 실행: 예약 시각 지난 것 1개를 인스타에 게시 → done\ 으로 이동
config.json     계정 아이디, 게시 시각(slots)
```

## "새 영상 예약해 줘" 절차
1. `git pull` (게시된 기록이 원격에 쌓이므로 먼저 받는다)
2. `python add_videos.py` → 새로 들어간 화와 예약 시각이 출력된다.
3. 새로 들어간 각 `queue\*\post.json`의 `caption`과 `hashtags`를 채운다 (아래 캡션 규칙).
4. `python add_videos.py --list`로 목록(예약 시각, 캡션 첫 줄)을 사용자에게 보여 준다.
5. 사용자가 확인하면 `git add -A` → `git commit -m "예약: <n>화 ..."` → `git push`.

## 캡션 규칙
- 1줄: 후킹 한 문장 (질문형 또는 반전, 25자 안팎). 인스타 릴스엔 제목 칸이 없으니 이 줄이 제목 역할.
- 빈 줄 뒤 2~3줄: 개념을 쉬운 말로 설명. 영상 주제(파일 이름의 주제)에 맞게, 과장·단정 없이 사실만.
- 빈 줄 뒤 마지막 줄: `유익한 정보를 더 알아보고 싶다면? 팔로우 👉 @mallang_knowledge`
- `hashtags`: 한국어 해시태그 5개 (# 없이), 주제 + 넓은 태그 섞기. 예: ["트래픽브레이크","교통상식","과학상식","지식릴스","점토애니메이션"]
- 해요체, 이모지는 1~2개까지.

## 그 밖의 요청
- "예약 목록 보여 줘": `python add_videos.py --list`
- "시험해 줘"(영상이 인스타에 받아지는지, 게시 안 함): `gh workflow run publish.yml -f mode=check -f post=<queue 폴더 이름>` → `gh run watch`
- "지금 바로 올려 줘": `gh workflow run publish.yml -f mode=now -f post=<폴더>`
- "게시 시각 바꿔 줘": config.json의 slots 수정 (이미 예약된 것은 post.json의 scheduled_at을 직접 고친다)

## 절대 규칙
- 인스타 토큰·계정 ID는 파일이나 커밋에 절대 넣지 않는다 (GitHub Secrets에만).
- 캡션이 비어 있는 게시물은 올라가지 않는다. 비워 둔 채 push해도 되지만 사용자에게 알린다.
