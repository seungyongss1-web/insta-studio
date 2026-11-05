# 자동 업로드 (인스타 예약 게시)

- GitHub 저장소 `seungyongss1-web/insta-studio` (예전 말랑지식 계정과 연결된 저장소)의 Actions가 매시 7분에 예약 시각이 지난 릴스를 1개씩 올린다.
- 인스타 연결은 시크릿 `IG_FACELESS_USER_ID`(계정 고유번호) + `IG_FACELESS_TOKEN`. 사용자 이름을 바꿔도 그대로 동작한다.
- 예약 추가: `python engine/queue_post.py episodes/NN` → `queue/<날짜-시각-epNN>/`에 reel.mp4 · cover.jpg · post.json 생성
- GitHub에 올리기: `올리기.bat` (Claude Code에서 실행할 때는 `올리기.bat auto` → 마지막에 멈추지 않음)
- 처음 실행하면 저장소에 남아 있던 예전 점토 영상 예약(queue)·기록(done)과 점토용 파일이 정리된다.
- 게시가 끝나면 done/으로 옮겨지고 영상 파일은 지워진다(원본은 episodes/에 있음).
- 게시 시각은 config.json의 slots (기본 매일 21:30, 하루 1편).
