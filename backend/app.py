"""
app.py
------
Servidor local do C5. Roda no seu próprio notebook (localhost) — não expõe
nada pra internet, só serve a interface que abre no navegador/Electron.

Endpoints:
  GET  /                      -> healthcheck simples
  WS   /ws/telemetry          -> transmite os dados do carro em tempo real
  POST /ask   {"text": "..."} -> pergunta pro C5 (local ou Gemini, automático)

Para rodar:
  uvicorn app:app --reload --host 127.0.0.1 --port 8000
"""

import os
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from obd_reader import OBDReader
import ai_engine
import tts
import stt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("c5.app")

app = FastAPI(title="C5 AI - Backend Local")

# Libera o frontend (que roda em outra porta/arquivo local) a chamar o backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # ambiente local, sem exposição externa
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uma única instância do leitor OBD2, compartilhada por toda a aplicação
obd_port = os.getenv("OBD_PORT") or None
force_demo = os.getenv("C5_FORCE_DEMO", "0") == "1"
reader = OBDReader(portstr=obd_port, demo_mode=force_demo)

# Guarda o último snapshot lido, para o /ask poder usar sem esperar o
# próximo ciclo do WebSocket
_latest_snapshot = {}


class Question(BaseModel):
    text: str


class TTSRequest(BaseModel):
    text: str
    voice: str | None = None


@app.get("/")
def healthcheck():
    return {
        "status": "ok",
        "obd_connected": reader.is_connected(),
        "demo_mode": reader.demo_mode,
    }


@app.websocket("/ws/telemetry")
async def telemetry_ws(websocket: WebSocket):
    """
    Envia os dados do carro a cada 1 segundo para quem estiver conectado
    (a interface fica ouvindo isso pra atualizar os mostradores em tempo
    real, tipo velocímetro, RPM etc.)
    """
    global _latest_snapshot
    await websocket.accept()
    logger.info("Cliente conectado ao WebSocket de telemetria.")
    try:
        while True:
            snapshot = reader.get_snapshot()
            _latest_snapshot = snapshot
            await websocket.send_json(snapshot)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("Cliente desconectado do WebSocket de telemetria.")


@app.post("/ask")
async def ask(question: Question):
    """
    Recebe uma pergunta de texto (vinda da digitação ou de
    voz-para-texto no frontend) e devolve a resposta do C5.
    """
    snapshot = _latest_snapshot or reader.get_snapshot()
    result = ai_engine.get_answer(question.text, snapshot)
    return result


@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Converte o texto recebido em áudio (mp3) e devolve o arquivo. Se o
    frontend enviar 'voice', usa essa voz; senão, usa a padrão do .env.
    """
    filepath = await tts.synthesize(request.text, voice=request.voice)
    return FileResponse(filepath, media_type="audio/mpeg", filename="c5-fala.mp3")


@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Recebe um áudio gravado no app (microfone) e devolve o texto
    transcrito, usando o Whisper local — não depende de internet nem do
    Google (o reconhecimento de voz do navegador não funciona dentro do
    Electron, por isso essa rota existe).
    """
    audio_bytes = await audio.read()
    text = stt.transcribe(audio_bytes)
    return {"text": text}


if __name__ == "__main__":
    import uvicorn
    # reload=True cria DOIS processos (um vigia o código, outro roda de
    # verdade) — e os dois tentam abrir a porta COM do OBD2 ao mesmo
    # tempo, o que trava a conexão real. Por isso fica desligado por
    # padrão; só ligue (C5_DEV_RELOAD=1) se estiver editando o código.
    #
    # Importante: com reload precisa passar "app:app" como texto (pro
    # uvicorn recarregar o arquivo sozinho quando mudar), mas isso faz
    # o Python importar este arquivo DUAS VEZES (uma como programa
    # principal, outra pelo nome "app") quando reload está desligado —
    # o que conectava no carro duas vezes. Por isso, sem reload, passamos
    # o "app" já carregado direto, sem reimportar.
    dev_reload = os.getenv("C5_DEV_RELOAD", "0") == "1"
    if dev_reload:
        uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
    else:
        uvicorn.run(app, host="127.0.0.1", port=8000)
