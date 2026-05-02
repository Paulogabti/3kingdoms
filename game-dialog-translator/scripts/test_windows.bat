@echo off
setlocal
if not exist .venv\Scripts\activate.bat (echo Ambiente virtual nao encontrado. Rode scripts\setup_windows.bat& exit /b 1)
call .venv\Scripts\activate.bat
pytest -q
