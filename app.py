from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
import whisper
import shutil
import os
import uuid
import threading
import time
import librosa

app = FastAPI()

print("Carregando Whisper large...")
model = whisper.load_model("large")
print("Modelo carregado.")

# ===== ESTADO GLOBAL =====
estado = {
    "percent": 0,
    "status": "Aguardando",
    "resultado": ""
}

# ===== HTML =====
HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Transcritor Local</title>
<style>
body {
    font-family: Arial, sans-serif;
    background: #f5f6fa;
    margin: 40px;
}
.container {
    max-width: 600px;
    background: white;
    padding: 25px;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}
.status {
    margin-top: 15px;
    font-size: 15px;
}
.percent {
    font-weight: bold;
    font-size: 18px;
    margin-top: 5px;
}
pre {
    background: #eee;
    padding: 10px;
    white-space: pre-wrap;
    margin-top: 15px;
}
</style>
</head>
<body>

<div class="container">
<h2>🎙️ Transcritor de Reuniões — Whisper Large</h2>

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
    }, 500);
}
</script>

</body>
</html>
"""

# ===== ROTAS =====
@app.get("/", response_class=HTMLResponse)
def index():
    return HTML

@app.get("/estado")
def get_estado():
    return estado

@app.post("/transcrever")
async def transcrever(file: UploadFile = File(...)):
    # ✔ SALVA O ARQUIVO AQUI (NO CONTEXTO DA REQUEST)
    nome_tmp = f"{uuid.uuid4()}_{file.filename}"
    with open(nome_tmp, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ✔ PASSA APENAS O CAMINHO PARA A THREAD
    threading.Thread(
        target=processar,
        args=(nome_tmp,),
        daemon=True
    ).start()

    return JSONResponse({"ok": True})

# ===== PROCESSAMENTO =====
def processar(caminho):
    global estado

    estado["percent"] = 0
    estado["status"] = "Calculando duração..."
    estado["resultado"] = ""

    duracao = librosa.get_duration(path=caminho)
    estimado = max(duracao * 1.6, 10)

    inicio = time.time()
    estado["status"] = "Transcrevendo..."

    def atualizar_percentual():
        while estado["percent"] < 99:
            elapsed = time.time() - inicio
            estado["percent"] = min(99, int((elapsed / estimado) * 100))
            time.sleep(0.5)

    threading.Thread(
        target=atualizar_percentual,
        daemon=True
    ).start()

    result = model.transcribe(caminho, language="pt")

    estado["resultado"] = result["text"]

    with open("transcricao.txt", "w", encoding="utf-8") as f:
        f.write(result["text"])

    os.remove(caminho)

    estado["percent"] = 100
    estado["status"] = "Transcrição concluída"
