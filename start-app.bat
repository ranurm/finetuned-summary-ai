@echo off
echo Starting AI Meeting Summary Tool...

REM Start the Python backend in a new window
start cmd /k "cd backend && python summary.py"

REM Wait a moment for the backend to initialize
timeout /t 3

REM Start the React frontend in this window
npm start 