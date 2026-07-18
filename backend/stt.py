"""
stt.py
------
Transcreve áudio (fala) em texto, 100% local — sem depender do Google
nem do Gemini. Usa o faster-whisper (versão otimizada do Whisper da
OpenAI que roda bem em CPU comum, sem precisar de placa de vídeo).

Por que isso existe: o reconhecimento de voz do navegador
(SpeechRecognition/webkitSpeechRecognition) NÃO funciona dentro de apps
Electron — o Google bloqueia esse serviço fora do Chrome de verdade. A
solução é gravar o áudio no app e mandar pra cá pra transcrever.

O primeiro uso baixa o modelo (~150MB pro tamanho "base"), depois disso
funciona offline.
"""

import os
import logging
import tempfile

logger = logging.getLogger("c5.stt")

MODEL_SIZE = os.getenv("C5_WHISPER_MODEL", "base")

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        logger.info(f"Carregando modelo Whisper '{MODEL_SIZE}' (primeira vez pode demorar, baixa o modelo)...")
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        logger.info("Modelo Whisper carregado.")
    return _model


def transcribe(audio_bytes: bytes, suffix: str = ".webm") -> str:
    """
    Recebe os bytes de um áudio (webm/ogg/wav/mp3, o faster-whisper decodifica
    sozinho) e retorna o texto transcrito em português.
    """
    model = _get_model()

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    # "Dica" de vocabulário: ajuda o Whisper a acertar nomes e termos
    # específicos deste app, que ele não conheceria de outra forma.
    vocab_hint = (
        "C5, Citroën, OBD2, RPM, Hydractive, Jonathas, Jordania, Luna, Lara, "
        "Dona Ana, Nivaldo, sonda lambda, combustível, câmbio, motor."
    )

    try:
        segments, _info = model.transcribe(
            tmp_path, language="pt", beam_size=1, initial_prompt=vocab_hint
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return text
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
