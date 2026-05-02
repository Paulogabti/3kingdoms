from __future__ import annotations

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

URL = "http://localhost:8501"


def main() -> int:
    root = Path(__file__).resolve().parent
    app_file = root / "app.py"
    if not app_file.exists():
        print("Erro: app.py não encontrado.")
        return 1

    cmd = [sys.executable, "-m", "streamlit", "run", str(app_file), "--server.headless=false"]
    try:
        proc = subprocess.Popen(cmd, cwd=root)
    except Exception:
        print("Falha ao iniciar Streamlit. Rode scripts/setup_windows.bat para instalar dependências.")
        return 1

    print(f"Aplicação iniciada em {URL}")
    time.sleep(2)
    webbrowser.open(URL)
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("Encerrando aplicação...")
        proc.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
