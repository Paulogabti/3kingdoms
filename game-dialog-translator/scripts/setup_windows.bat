@echo off
setlocal
where python >nul 2>nul || (echo Python nao encontrado. Instale Python 3.11+ e tente novamente.& exit /b 1)
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if exist requirements-dev.txt (
  set /p INSTALL_DEV=Instalar dependencias de desenvolvimento (requirements-dev.txt)? [Y/N]:
  if /I "%INSTALL_DEV%"=="Y" pip install -r requirements-dev.txt
)
if not exist .env if exist .env.example copy .env.example .env >nul
echo Setup concluido. Edite .env com OPENAI_API_KEY e execute scripts\run_windows.bat
