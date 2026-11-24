@echo off
cd /d "%~dp0"
py -3 -m clutchsift
if errorlevel 1 (
  echo.
  echo Could not start ClutchSift. Check Python and FFmpeg installation.
  pause
)
