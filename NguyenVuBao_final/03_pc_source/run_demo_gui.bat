@echo off
title Demo Nen Anh IoT: TinyCAE INT8 vs. JPEG tren ESP32 (Tkinter Desktop)
color 0a
echo =======================================================================
echo   DEMO HE THONG NEN ANH IOT: TINYCAE INT8 VS. JPEG TREN ESP32 (GUI)
echo   Tac gia: Nguyen Vu Bao (MSSV: 23110079)
echo   Giang vien huong dan: Thay Ho Nhut Minh
echo =======================================================================
echo.

set PY_EXE=python
if exist "%~dp0..\..\.venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0..\..\.venv\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0.venv\Scripts\python.exe"
)

echo Dang su dung Python: %PY_EXE%
echo [1/1] Khoi dong Desktop GUI Demo tren ESP32...
echo.
"%PY_EXE%" "%~dp0demo\gui_app.py"

pause
