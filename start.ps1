Write-Host "Iniciando Transcritor Web Local"

if (!(Test-Path venv)) {
    Write-Host "Criando ambiente virtual..."
    python -m venv venv
}

Write-Host "Ativando ambiente virtual..."
.\venv\Scripts\Activate.ps1

Write-Host "Atualizando pip..."
python -m pip install --upgrade pip

Write-Host "Instalando dependências..."
pip install -r requirements.txt

Write-Host "Iniciando servidor..."
uvicorn app:app --host 127.0.0.1 --port 8000

Pause
