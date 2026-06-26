@echo off
title MelodyHub - Clean Data

echo ====================================
echo   MelodyHub Data Cleanup
echo ====================================
echo.
echo This will delete:
echo   - Database (all songs/playlists)
echo   - Downloaded music files
echo   - Cover cache
echo.
set /p CONFIRM="Confirm? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Cancelled.
    pause
    exit /b
)

echo.
echo Cleaning...

if exist "backend\melodyhub.db" del /Q "backend\melodyhub.db"
if exist "Music\*.mp3" del /Q "Music\*.mp3"
if exist "Music\*.flac" del /Q "Music\*.flac"
if exist "Music\covers" rmdir /S /Q "Music\covers"

echo.
echo Done! All data cleared.
pause
