@echo off
echo Starting AI Meeting Summary Tool...

REM Check if concurrently is installed
call npm list -g concurrently >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing concurrently package...
    call npm install
)

REM Run the application
echo Running both backend and frontend...
call npm run app

REM If the script exits, keep the window open
pause 