@echo off
echo Starting O2C Graph System on Windows...
echo.

:: 1. Start Backend in a new window
echo Starting Backend on port 8000...
cd backend
start "Dodge AI Backend" cmd /c "venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000"
cd ..

:: 2. Start Frontend in a new window
echo Starting Frontend on port 5173...
cd dodge-ui
start "Dodge AI Frontend" cmd /c "npm run dev -- --host 0.0.0.0 --port 5173"
cd ..

echo.
echo ------------------------------------------------
echo Services starting in separate command windows.
echo Application will be available at: http://localhost:5173
echo ------------------------------------------------
pause
