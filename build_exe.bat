@echo off
setlocal
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo Python 3.11 was not found. Install Python 3.11 x64 from python.org first.
  pause
  exit /b 1
)
py -3.11 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --windowed --name StudyMonitor --collect-all mediapipe --collect-all cv2 --collect-all pygame --add-data "Kyu_Nhi_Ho_Rhi_Padhai_Meme_Download.mp3;." --add-data "Padhai_Likhai_Karo_Ias_Bano_Meme_Video_Download_From_Indian_Meme_Template.mp3;." --add-data "Tumse_Na_Ho_Payega_Meme_Video_Download.mp3;." --add-data "Kyu_Nhi_Ho_Rhi_Padhai_Meme_Download(1).mp3;." --add-data "wm_6537c8b9.mp3;." study_monitor.py
if errorlevel 1 (
  echo Build failed. Read the error above and check README.md troubleshooting.
  pause
  exit /b 1
)
echo.
echo Build complete: dist\StudyMonitor\StudyMonitor.exe
echo This is a folder-based build; keep the entire dist\StudyMonitor folder together.
pause
