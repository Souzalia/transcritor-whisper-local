# ==========================================
# TRANSCRITOR LOCAL - START SCRIPT
# Whisper Large + Relatório IA (Mistral)
# ==========================================

Write-Host ""
Write-Host "=========================================="
Write-Host "Transcritor Local - Inicialização"
Write-Host "=========================================="
Write-Host ""

# ------------------------------------------
# 1️⃣ Verificar Python
# ------------------------------------------
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python não encontrado."
    Write-Host "Instale o Python 3.10 ou 3.11 em:"
    Write-Host "https://www.python.org/downloads/"
    Write-Host ""
    Write-Host "Durante a instalação marque: Add Python to PATH"
    pause
    exit
}

# ------------------------------------------
# 2️⃣ Criarr ambiente virtual (se não existir)
# ------------------------------------------
if (!(Test-Path venv)) {
    Write-Host "Criando ambiente virtual..."
    python -m venv venv
}

# ------------------------------------------
# 3️⃣ Ativar ambiente virtual
# ------------------------------------------
Write-Host "Ativando ambiente virtual..."
& .\venv\Scripts\Activate.ps1

# ------------------------------------------
# 4️⃣ Atualizar pip e instalar dependências
# ------------------------------------------
Write-Host "Instalando dependências..."
python -m pip install --upgrade pip | Out-Null
pip install -r requirements.txt

# ------------------------------------------
# 5️⃣ Verificar FFmpeg
# ------------------------------------------
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "FFmpeg não encontrado."
    Write-Host "Instale em: https://ffmpeg.org/download.html"
    Write-Host "E adicione ao PATH do Windows."
    pause
    exit
}

# ------------------------------------------
# 6️⃣ Verificar Ollama (opcional)
# ------------------------------------------
$ollamaDisponivel = $true

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "Ollama NÃO encontrado."
    Write-Host "Relatório com IA ficará DESABILITADO."
    Write-Host "Instale em: https://ollama.com"
    $ollamaDisponivel = $false
}

# ------------------------------------------
# 7️⃣ Verificar modelo Mistral (se Ollama existir)
# ------------------------------------------
if ($ollamaDisponivel) {
    $mistralInstalado = ollama list | Select-String "mistral"

    if (-not $mistralInstalado) {
        Write-Host ""
        Write-Host "Modelo Mistral não encontrado."
        Write-Host "Baixando modelo (pode demorar alguns minutos)..."
        ollama pull mistral
    }
}

# ------------------------------------------
# 8️⃣ Iniciar servidor FastAPI
# ------------------------------------------
Write-Host ""
Write-Host "Iniciando Transcritor Local..."
Write-Host ""
Write-Host "Após carregar, abra o navegador em:"
Write-Host "   http://localhost:8000"
Write-Host ""

uvicorn app:app --host 127.0.0.1 --port 8000

pause
