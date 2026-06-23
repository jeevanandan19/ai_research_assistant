@echo off
title AI Research Assistant
cd /d "D:\major project\ai_research_assistant\ai_research_assistant"

echo.
echo =====================================================
echo   AI Research Assistant Agent
echo =====================================================
echo.

REM Check .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Copy .env.example to .env and add your GOOGLE_API_KEY
    pause
    exit /b 1
)

REM Check GOOGLE_API_KEY is set (basic check)
findstr /i "GOOGLE_API_KEY=your_google_api_key_here" .env >nul 2>&1
if %errorlevel%==0 (
    echo.
    echo WARNING: You have not set your GOOGLE_API_KEY in .env
    echo Open .env and replace "your_google_api_key_here" with your real key.
    echo Get a free key at: https://aistudio.google.com/app/apikey
    echo.
    pause
)

echo Starting server on http://localhost:5000
echo Press Ctrl+C to stop.
echo.
python app.py
pause
