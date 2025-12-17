from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
import whisper
import shutil
import os
import uuid
import threading
import time
import librosa
import subprocess

# ================================
# APP
# ================================
app = FastAPI()

print("Carregando Whisper large...")
model = whisper.load_model("large")
print("Modelo carregado.")

# ================================
# ESTADOS GLOBAIS (THREAD-SAFE)
# ================================
estado = {
    "percent": 0,
    "status": "Aguardando arquivo",
    "resultado": ""
}
estado_relatorio = {
    "percent": 0,
    "status": "Aguardando relatório",
    "resultado": ""
}

estado_lock = threading.Lock()
estado_relatorio_lock = threading.Lock()

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
body { font-family: Arial; background:#f5f6fa; margin:40px; }
.container { max-width:650px; background:white; padding:35px; border-radius:12px; box-shadow:0 0 15px rgba(0,0,0,0.1);}
h2 { margin-top:0; color:#4a6cf7; }

button {
    padding:10px 16px;
    border:none;
    border-radius:6px;
    background:#4a6cf7;
    color:white;
    cursor:pointer;
    margin-right:10px;
    font-size:14px;
}

button:hover { background:#3b5de3; }

button:disabled {
    background:#bfc6e0;
    cursor:not-allowed;
    opacity:0.7;
}

.status { margin-top:20px; font-size:15px; color:#444; }
.percent { margin-top:6px; font-size:24px; font-weight:bold; color:#4a6cf7; background:transparent; border:none; box-shadow:none; display:inline-block; }

pre { margin-top:30px; padding:18px; background:#f1f3f6; border-radius:8px; white-space:pre-wrap; font-size:14px; line-height:1.5; border:none; box-shadow:none; }

.file-input-wrapper { position: relative; overflow: hidden; display: inline-block; }
.file-input-button { border: none; color: white; background-color: #4a6cf7; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-size: 14px; }
.file-input-button:hover { background-color: #3b5de3; }

.file-input-wrapper input[type=file] {
    font-size: 100px;
    position: absolute;
    left: 0;
    top: 0;
    opacity: 0;
    cursor: pointer;
}
</style>
</head>
<body>
<div class="container">
<h2>🎙️ Transcritor — Whisper Large</h2>

<div class="file-input-wrapper">
  <button class="file-input-button" type="button">Selecionar arquivo</button>
  <span id="nome_arquivo" style="margin-left:4px; font-size:14px; color:#333;">
    Nenhum arquivo selecionado
  </span>
  <input type="file" id="file" accept="audio/*,video/*">
</div>

<br><br>

<button onclick="enviar()">Iniciar Transcrição</button>

<button
  id="btnRelatorio"
  onclick="gerarRelatorio()"
  disabled
>
  Gerar relatório com IA
</button>

<div class="status" id="status">Aguardando arquivo...</div>
<div class="percent" id="percent">0%</div>

<div class="status" id="status_relatorio"></div>
<div class="percent" id="percent_relatorio"></div>

<pre id="resultado"></pre>
</div>

<script>
const fileInput = document.getElementById('file');
const nomeArquivo = document.getElementById('nome_arquivo');
const btnRelatorio = document.getElementById('btnRelatorio');

document.querySelector('.file-input-button').addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        nomeArquivo.innerText = fileInput.files[0].name;
    } else {
        nomeArquivo.innerText = "Nenhum arquivo selecionado";
    }
});

async function enviar() {
    if (!fileInput.files.length) {
        alert("Selecione um arquivo.");
        return;
    }

    document.getElementById("status").innerText = "Preparando arquivo...";
    document.getElementById("percent").innerText = "0%";
    document.getElementById("resultado").innerText = "";

    // 🔒 desabilita relatório enquanto transcreve
    btnRelatorio.disabled = true;

    let form = new FormData();
    form.append("file", fileInput.files[0]);

    await fetch("/transcrever", { method:"POST", body:form });
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

            // ✅ habilita relatório APENAS após transcrição
            btnRelatorio.disabled = false;
        }
    }, 400);
}

async function gerarRelatorio() {
    document.getElementById("status_relatorio").innerText = "Gerando relatório...";
    document.getElementById("percent_relatorio").innerText = "0%";

    await fetch("/gerar_relatorio", { method:"POST" });
    acompanharRelatorio();
}

function acompanharRelatorio() {
    let timer = setInterval(async () => {
        let r = await fetch("/estado_relatorio");
        let data = await r.json();

        document.getElementById("status_relatorio").innerText = data.status;
        document.getElementById("percent_relatorio").innerText = data.percent + "%";

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

@app.get("/estado_relatorio")
def get_estado_relatorio():
    with estado_relatorio_lock:
        return estado_relatorio.copy()

@app.post("/transcrever")
async def transcrever(file: UploadFile = File(...)):
    nome_tmp = f"{uuid.uuid4()}_{file.filename}"
    with open(nome_tmp, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    threading.Thread(target=processar, args=(nome_tmp,), daemon=True).start()
    return JSONResponse({"ok": True})

@app.post("/gerar_relatorio")
async def gerar_relatorio():
    threading.Thread(target=processar_relatorio, daemon=True).start()
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
    chunk = 30

    while tempo_processado < duracao_total:
        inicio = tempo_processado
        fim = min(tempo_processado + chunk, duracao_total)

        result = model.transcribe(
            caminho,
            language="pt",
            verbose=False,
            clip_timestamps=f"{inicio},{fim}"
        )
        texto_final.append(result.get("text",""))
        tempo_processado = fim

        with estado_lock:
            estado["percent"] = min(99, int((tempo_processado/duracao_total)*100))

    with estado_lock:
        estado["resultado"] = "".join(texto_final)
        estado["percent"] = 100
        estado["status"] = "Transcrição concluída"

    with open("transcricao.txt", "w", encoding="utf-8") as f:
        f.write(estado["resultado"])

    os.remove(caminho)

# ================================
# RELATÓRIO COM MISTRAL (português)
# ================================
def processar_relatorio():
    global estado_relatorio, estado

    # ================================
    # 1️⃣ Inicialização do estado
    # ================================
    with estado_relatorio_lock:
        estado_relatorio["percent"] = 0
        estado_relatorio["status"] = "Gerando relatório..."
        estado_relatorio["resultado"] = ""

    # Texto base da transcrição
    with estado_lock:
        texto_base = estado["resultado"]

    if not texto_base.strip():
        with estado_relatorio_lock:
            estado_relatorio["status"] = "Nenhuma transcrição encontrada"
            estado_relatorio["percent"] = 100
        return

    # ================================
    # 2️⃣ Definição dos chunks (seções)
    # ================================
    secoes = [
        ("Visão geral da reunião",
         "Faça um resumo objetivo do contexto, participantes e objetivo da reunião."),
        ("Principais decisões",
         "Liste as decisões tomadas durante a reunião de forma clara."),
        ("Ações a tomar",
         "Liste ações, responsáveis (se houver) e prazos."),
        ("Observações importantes",
         "Inclua pontos relevantes, alertas, riscos ou alinhamentos."),
        ("Resumo final",
         "Faça um fechamento resumindo os principais pontos.")
    ]

    total_secoes = len(secoes)
    relatorio_final = []

    # ================================
    # 3️⃣ Geração seção por seção
    # ================================
    for i, (titulo, instrucao) in enumerate(secoes):
        with estado_relatorio_lock:
            estado_relatorio["status"] = f"Gerando: {titulo}..."

        prompt = f"""
Você é um assistente especializado em gerar atas e relatórios profissionais.
Use EXCLUSIVAMENTE o idioma português (Brasil).
NÃO utilize palavras em inglês.
NÃO traduza nomes próprios.
NÃO adicione informações que não estejam no texto.

TEXTO DA REUNIÃO:
-----------------
{texto_base}
-----------------

TAREFA:
Gere a seção do relatório chamada:
"{titulo}"

ORIENTAÇÃO:
{instrucao}

FORMATO:
- Linguagem formal e clara
- Frases completas
- Sem listas em inglês
"""

        try:
            # Chamada real ao Mistral via Ollama
            resposta = subprocess.run(
                ["ollama", "run", "mistral"],
                input=prompt,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True
            ).stdout.strip()

        except Exception as e:
            resposta = f"[Erro ao gerar a seção '{titulo}': {str(e)}]"

        relatorio_final.append(f"\n### {titulo}\n{resposta}\n")

        # Atualiza progresso
        with estado_relatorio_lock:
            estado_relatorio["percent"] = int(((i + 1) / total_secoes) * 100)

    # ================================
    # 4️⃣ Finalização
    # ================================
    resultado = "\n".join(relatorio_final)

    with estado_relatorio_lock:
        estado_relatorio["resultado"] = resultado
        estado_relatorio["status"] = "Relatório concluído"
        estado_relatorio["percent"] = 100

    with open("relatorio.txt", "w", encoding="utf-8") as f:
        f.write(resultado)
