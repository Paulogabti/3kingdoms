@echo off
setlocal
if not exist .venv\Scripts\activate.bat (echo Ambiente virtual nao encontrado. Rode scripts\setup_windows.bat& exit /b 1)
call .venv\Scripts\activate.bat
pip install pyinstaller >nul
pyinstaller --noconfirm --onefile --name GameDialogTranslatorPTBR launcher.py
if not exist dist\GameDialogTranslatorPTBR mkdir dist\GameDialogTranslatorPTBR
copy dist\GameDialogTranslatorPTBR.exe dist\GameDialogTranslatorPTBR\ >nul
copy app.py dist\GameDialogTranslatorPTBR\ >nul
xcopy src dist\GameDialogTranslatorPTBR\src\ /E /I /Y >nul
xcopy samples dist\GameDialogTranslatorPTBR\samples\ /E /I /Y >nul
xcopy scripts dist\GameDialogTranslatorPTBR\scripts\ /E /I /Y >nul
copy .env.example dist\GameDialogTranslatorPTBR\ >nul
copy README.md dist\GameDialogTranslatorPTBR\ >nul
copy requirements.txt dist\GameDialogTranslatorPTBR\ >nul
echo Build finalizado em dist\GameDialogTranslatorPTBR
