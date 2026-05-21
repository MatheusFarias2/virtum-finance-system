@echo off
setlocal
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller --clean --noconfirm VirtumFinance.spec
echo.
echo Build finalizado. O executavel fica em: dist\VirtumFinance\VirtumFinance.exe
pause
