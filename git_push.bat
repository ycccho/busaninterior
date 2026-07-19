@echo off
chcp 65001 > nul
echo ===================================================
echo [Git Push Automation] 로컬 변경사항 원격 전송을 시작합니다.
echo ===================================================

:: Check if git repository is set up
git rev-parse --is-inside-work-tree > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git 저장소가 아닙니다. git init 및 remote 설정을 먼저 완료해 주세요.
    pause
    exit /b
)

:: Git status check
echo.
echo [1/3] 변경된 파일들을 스테이징 영역에 추가합니다...
git add .

:: Commit files
echo.
echo [2/3] 변경 사항을 로컬에 커밋합니다...
git commit -m "Auto-update: 부산 병원 인테리어 웹사이트 수정 및 SEO 최적화 완료"

:: Push to remote main branch
echo.
echo [3/3] 원격 저장소(origin main)로 푸시합니다...
git push origin main

if errorlevel 1 (
    echo.
    echo [ERROR] 깃 푸시 과정에서 오류가 발생했습니다. 네트워크 연결 또는 권한 설정을 확인하세요.
) else (
    echo.
    echo ===================================================
    echo [SUCCESS] 깃 푸시가 성공적으로 완료되었습니다!
    echo ===================================================
)

pause
