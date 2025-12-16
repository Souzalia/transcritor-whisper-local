# 🎙️ Transcritor Web Local de Reuniões (Whisper Large)

👉 Caso não seja a primeira vez em que faça uso do Transcritor então acesse a pasta transcritor-whisper-local-main, clique com o botão direito do mouse sobre start.ps1 e escolha Executar com o PowerShell.

Este aplicativo permite **transcrever áudios e vídeos para texto em português**, usando o modelo **Whisper Large**, diretamente no seu computador.

👉 **Não usa internet para transcrever** (apenas para baixar o modelo na primeira vez).
👉 **Não tem custo**.
👉 Funciona pelo **navegador**, de forma simples.

---

## 🧠 O que este aplicativo faz

- Transcreve **áudios e vídeos** (reuniões, entrevistas, aulas, etc.)
- Usa **Whisper Large** (maior qualidade)
- Mostra **porcentagem de progresso** durante a transcrição
- Salva automaticamente o texto em um arquivo `transcricao.txt`

---

## 💻 Requisitos (uma única vez)

Antes de usar, o computador precisa ter:

### 1️⃣ Python instalado
- Versão recomendada: **Python 3.10 ou 3.11**
- Download:
  https://www.python.org/downloads/

⚠️ Durante a instalação, marque obrigatoriamente:
☑ **Add Python to PATH**

---

### 2️⃣ FFmpeg instalado
O FFmpeg é necessário para ler áudios e vídeos.

⚠️ Instale o FFmpeg no Windows
https://ffmpeg.org/download.html

(adicione ao PATH)

Para testar, abra o PowerShell e digite:
```powershell
ffmpeg -version
```
Se aparecer a versão, está correto.

---

## 📂 Estrutura da pasta

Em Code (canto superior direito) faça o download zip
Você receberá uma pasta parecida com esta:

```
TranscritorWebLocal
 ├── app.py
 ├── requirements.txt
 ├── start.ps1
 └── README.md
```

⚠️ **Não apague nenhum arquivo**.

---

## ▶️ Como executar o transcritor

### 1️⃣ Executar o aplicativo

1. Clique com o botão direito no arquivo:
   ```
   start.ps1
   ```
2. Escolha:
   **Executar com PowerShell**

📌 Na **primeira execução**, o programa irá:
- Criar o ambiente automaticamente
- Baixar o modelo Whisper Large (demora alguns minutos)

Aguarde até aparecer algo como:
```
Uvicorn running on http://127.0.0.1:8000
```

---

### 2️⃣ Abrir no navegador

Abra o navegador (Chrome, Edge ou Firefox) e acesse:

```
http://localhost:8000
```

A tela do transcritor será exibida.

---

### 3️⃣ Usar o transcritor

1. Clique em **Selecionar arquivo**
2. Escolha um áudio ou vídeo
3. Clique em **Iniciar Transcrição**
4. Aguarde a conclusão

Durante o processo, será exibida uma **porcentagem (%)** indicando o andamento.

---

## 📄 Arquivo gerado

Ao final da transcrição:

- O texto aparece na tela
- Um arquivo é criado automaticamente:
  ```
  transcricao.txt
  ```

Ele fica na **mesma pasta do aplicativo**.

---

## 🎧 Formatos suportados

### Áudio
- WAV (recomendado)
- MP3
- M4A
- FLAC

### Vídeo
- MP4 (recomendado)
- MOV
- WEBM

⚠️ O vídeo precisa conter trilha de áudio.

---

## ⏱️ Observações importantes

- A transcrição **pode demorar**, dependendo:
  - Do tamanho do arquivo
  - Da potência do computador
- Arquivos longos = tempo maior
- Durante a execução, **não feche o PowerShell**

---

## 🔐 Aviso de segurança do Windows

Se o Windows bloquear o script, execute **uma única vez** no PowerShell:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Depois disso, o aplicativo funcionará normalmente.

---

## ❓ Problemas comuns

### ❌ FFmpeg não encontrado
Mensagem parecida com:
```
FileNotFoundError: ffmpeg
```
➡️ Verifique se o FFmpeg está no PATH corretamente.

---

### ❌ Página não abre
Verifique se no PowerShell aparece:
```
Uvicorn running on http://127.0.0.1:8000
```

Se não aparecer, feche tudo e execute `start.ps1` novamente.

---

## 🧩 Limitações

- Um usuário por vez
- Uso local (não acessível pela internet)
- Não indicado para muitos usuários simultâneos

Essas limitações são normais para uma aplicação local e gratuita.

---

## ✅ Conclusão

Este transcritor oferece:

✔ Alta qualidade (Whisper Large)
✔ Execução local
✔ Interface simples
✔ Sem custo
✔ Sem dependência de nuvem

Se tiver dúvidas, consulte este README novamente ou peça suporte técnico.

---

**Fim do manual.**

