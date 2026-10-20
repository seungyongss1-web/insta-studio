# 점토 영상 자동 업로드

점토 설명 영상을 인스타그램 @mallang_knowledge 에 매일 13:00·18:00(한국시간) 자동으로 올린다.

1. 새 영상을 `점토\영상`, 썸네일을 `점토\썸네일`에 저장
2. `새영상예약.bat` 더블클릭 → Claude Code가 예약·캡션 작성 → 확인 후 push
3. 예약 시각이 되면 GitHub Actions가 게시 (컴퓨터가 꺼져 있어도 됨)

시크릿: `IG_FACELESS_TOKEN`, `IG_FACELESS_USER_ID` (60일마다 토큰 갱신, 또는 `GH_PAT`을 넣으면 자동 갱신)
