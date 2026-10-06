@echo off
title Kiem Tra Phan Cung Bo Mach ESP32-CAM
color 0b
echo =======================================================================
echo   CHUONG TRINH KIEM TRA PHAN CUNG BO MACH ESP32-CAM (DIAGNOSTICS)
echo   De tai: TinyCAE INT8 vs. JPEG tren ESP32 - Nguyen Vu Bao (23110079)
echo =======================================================================
echo.
echo [1/2] Kich hoat moi truong Python...
call "%~dp0.venv\Scripts\activate.bat"

echo [2/2] Chay chan doan ket noi, UART, Bo nho, JPEG va TinyCAE...
echo.
"%~dp0.venv\Scripts\python.exe" "%~dp0host\serial_client\kiem_tra_mach.py"

echo.
echo =======================================================================
echo Nhan phim bat ky de thoat...
pause >nul
