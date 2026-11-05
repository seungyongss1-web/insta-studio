@echo off
chcp 65001 >nul
cd /d "%~dp0"
where git >nul 2>nul || (echo [오류] Git이 설치되어 있지 않아요. https://git-scm.com 에서 설치 후 다시 실행하세요. & pause & exit /b 1)
set REPO=https://github.com/seungyongss1-web/insta-studio.git
if not exist ".git" (
  rem 처음 한 번: 기존 GitHub 저장소에 이 폴더를 연결. 저장소에 남아 있던 예전 예약·기록은 이번 커밋에서 정리된다.
  git init -b main
  git remote add origin %REPO%
  git fetch origin main
  git reset --mixed origin/main >nul
) else (
  git pull --rebase origin main
)
if exist "_workflows\*.yml" (
  if not exist ".github\workflows" mkdir ".github\workflows"
  copy /y "_workflows\*.yml" ".github\workflows\" >nul
)
git config user.name >nul 2>nul || git config user.name "seungyongss1-web"
git config user.email >nul 2>nul || git config user.email "seungyongss1-web@users.noreply.github.com"
git add -A
git commit -m "예약 게시물 갱신" >nul 2>nul
git push -u origin main
if errorlevel 1 (echo. & echo [실패] 위 메시지를 Claude에게 보여 주세요.) else (echo. & echo [완료] 예약이 GitHub에 올라갔어요.)
if /i not "%1"=="auto" pause
