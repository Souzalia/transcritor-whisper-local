from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
import whisper
import shutil
import os
import uuid
import threading
import time
import librosa

# ================================
# APP
# ================================
app = FastAPI()

print("Carregando Whisper large...")
model = whisper.load_model("large")
print("Modelo carregado.")

# ================================
# ESTADO GLOBAL (THREAD-SAFE)
# ================================
estado = {
    "percent": 0,
    "status": "Aguardando arquivo",
    "resultado": ""
}

estado_lock = threading.Lock()

# ================================
# HTML
# ================================
HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Transcritor Local</title>

<style>
* {
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: #f5f6fa;
    margin: 40px;
}

.container {
    max-width: 620px;
    background: white;
    padding: 30px;
    border-radius: 12px;
}

h2 {
    margin-top: 0;
}

button {
    padding: 10px 16px;
    border: none;
    border-radius: 6px;
    background: #4a6cf7;
    color: white;
    font-size: 14px;
    cursor: pointer;
}

button:hover {
    background: #3b5de3;
}

.status {
    margin-top: 20px;
    font-size: 15px;
    color: #444;
}

.percent {
    margin-top: 6px;
    font-size: 24px;
    font-weight: bold;
    color: #4a6cf7;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    display: inline-block;
}

pre {
    margin-top: 30px;
    padding: 18px;
    background: #f1f3f6;
    border-radius: 8px;
    white-space: pre-wrap;
    font-size: 14px;
    line-height: 1.5;
    border: none;
    box-shadow: none;
}
</style>

</head>
<body>

<div class="container">
<h2>🎙️ Transcritor — Whisper Large</h2>

<input type="file" id="file" accept="audio/*,video/*">
<br><br>
<button onclick="enviar()">Iniciar Transcrição</button>

<div class="status" id="status">Aguardando arquivo...</div>
<div class="percent" id="percent">0%</div>

<pre id="resultado"></pre>
</div>

<script>
async function enviar() {
    let fileInput = document.getElementById("file");
    if (!fileInput.files.length) {
        alert("Selecione um arquivo.");
        return;
    }

    document.getElementById("status").innerText = "Preparando arquivo...";
    document.getElementById("percent").innerText = "0%";
    document.getElementById("resultado").innerText = "";

    let form = new FormData();
    form.append("file", fileInput.files[0]);

    await fetch("/transcrever", {
        method: "POST",
        body: form
    });

    acompanhar();
}

function acompanhar() {
    let timer = setInterval(async () => {
        let r = await fetch("/estado");
        let data = await r.json();

        document.getElementById("status").innerText = data.status;
        document.getElementById("percent").innerText = data.percent + "%";

        if (data.percent >= 100) {
            clearInterval(timer);
            document.getElementById("resultado").innerText = data.resultado;
        }
    }, 400);
}
</script>

</body>
</html>
"""

# ================================
# ROTAS
# ================================
@app.get("/", response_class=HTMLResponse)
def index():
    return HTML

@app.get("/estado")
def get_estado():
    with estado_lock:
        return estado.copy()

@app.post("/transcrever")
async def transcrever(file: UploadFile = File(...)):
    nome_tmp = f"{uuid.uuid4()}_{file.filename}"

    with open(nome_tmp, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    threading.Thread(
        target=processar,
        args=(nome_tmp,),
        daemon=True
    ).start()

    return JSONResponse({"ok": True})

# ================================
# PROCESSAMENTO
# ================================
def processar(caminho):
    global estado

    with estado_lock:
        estado["percent"] = 0
        estado["status"] = "Calculando duração..."
        estado["resultado"] = ""

    duracao_total = librosa.get_duration(path=caminho)

    with estado_lock:
        estado["status"] = "Transcrevendo..."

    texto_final = []
    tempo_processado = 0.0
    chunk = 30  # segundos

    while tempo_processado < duracao_total:
        inicio = tempo_processado
        fim = min(tempo_processado + chunk, duracao_total)

        result = model.transcribe(
            caminho,
            language="pt",
            verbose=False,
            clip_timestamps=f"{inicio},{fim}"
        )

        if "text" in result:
            texto_final.append(result["text"])

        tempo_processado = fim

        progresso = int((tempo_processado / duracao_total) * 100)

        with estado_lock:
            estado["percent"] = min(99, progresso)

    texto_final_str = "".join(texto_final)

    with estado_lock:
        estado["resultado"] = texto_final_str
        estado["percent"] = 100
        estado["status"] = "Transcrição concluída"

    with open("transcricao.txt", "w", encoding="utf-8") as f:
        f.write(texto_final_str)

    os.remove(caminho)

