"""
tts.py
------
Converte texto em áudio falado, em português, com uma voz suave.
Usa o edge-tts (gratuito, boa qualidade, roda em segundos). Precisa de
internet só nesta parte — a leitura do carro continua 100% local.
"""

import os
import uuid
import logging
import edge_tts

logger = logging.getLogger("c5.tts")

# Vozes em pt-BR disponíveis no edge-tts:
#   pt-BR-FranciscaNeural  -> feminina, suave (padrão do C5)
#   pt-BR-AntonioNeural    -> masculina
VOICE = os.getenv("C5_VOICE", "pt-BR-FranciscaNeural")

TMP_DIR = os.path.join(os.path.dirname(__file__), "tts_cache")
os.makedirs(TMP_DIR, exist_ok=True)


async def synthesize(text: str, voice: str = None) -> str:
    """
    Gera um arquivo .mp3 com a fala do texto recebido e retorna o caminho
    do arquivo. Se 'voice' for passado, usa essa voz; senão, usa a
    configurada no .env (C5_VOICE). O chamador é responsável por
    servir/apagar o arquivo.
    """
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(TMP_DIR, filename)

    selected_voice = voice or VOICE
    communicate = edge_tts.Communicate(text, selected_voice, rate="+2%")
    await communicate.save(filepath)

    return filepath
