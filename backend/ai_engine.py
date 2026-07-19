"""
ai_engine.py
------------
Cérebro de decisão do C5.

Regra de ouro do projeto: perguntas sobre o CARRO nunca dependem de
internet. Elas são respondidas na hora, localmente, usando os dados que o
obd_reader.py já leu do veículo.

Qualquer outra pergunta (perguntas gerais tipo ChatGPT) é respondida por um
LLM local (Ollama, de graça, sem internet) por padrão. Também dá pra trocar
pra nuvem (OpenAI) via variável de ambiente, se preferir.
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import car_info
import family_info
import small_talk

load_dotenv()

logger = logging.getLogger("c5.ai_engine")

# Modo do "cérebro" pra perguntas gerais: "local" (Ollama, de graça, sem
# internet) ou "cloud" (OpenAI, precisa de crédito cadastrado). Padrão é
# local, pra não depender mais de cota/cartão de crédito.
AI_PROVIDER = os.getenv("AI_PROVIDER", "local")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("biblioteca openai não instalada. Rode: pip install -r requirements.txt")


# ---------------------------------------------------------------------------
# 1. Classificador simples: a pergunta é sobre o carro ou é geral?
# ---------------------------------------------------------------------------

CAR_KEYWORDS = [
    "rpm", "motor", "veloc", "velocidade", "combust", "gasolina", "tanque",
    "bateria", "temperatura", "temp do motor", "acelera", "km/h",
    "carro", "veículo", "veiculo", "óleo", "oleo", "voltagem", "consumo",
    "carga do motor", "sonda lambda", "sonda", "o2", "trim de combust",
    "fluxo de ar", "maf", "ar de admissão", "temperatura do ar",
    "código de falha", "codigo de falha", "falha", "erro do motor",
    "dtc", "luz de injeção", "luz da injeção", "check engine", "status",
]

DATETIME_KEYWORDS = [
    "que dia é hoje", "que dia e hoje", "qual a data", "que horas são",
    "que horas sao", "que dia da semana", "dia da semana hoje",
    "que mês estamos", "que mes estamos", "que ano estamos",
]

DIAS_SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
               "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
          "agosto", "setembro", "outubro", "novembro", "dezembro"]


def is_datetime_question(text: str) -> bool:
    text_low = text.lower()
    return any(kw in text_low for kw in DATETIME_KEYWORDS)


def answer_datetime_question(text: str) -> str:
    """Responde com data/hora local do próprio computador, sem internet."""
    now = datetime.now()
    text_low = text.lower()
    dia_semana = DIAS_SEMANA[now.weekday()]
    mes = MESES[now.month - 1]

    if "hora" in text_low:
        return f"Agora são {now.strftime('%H:%M')}."

    if "dia da semana" in text_low:
        return f"Hoje é {dia_semana}."

    if "ano" in text_low:
        return f"Estamos em {now.year}."

    if "mês" in text_low or "mes" in text_low:
        return f"Estamos em {mes} de {now.year}."

    # "que dia é hoje" / "qual a data" -> resposta completa
    return f"Hoje é {dia_semana}, {now.day} de {mes} de {now.year}."


def is_car_question(text: str) -> bool:
    text_low = text.lower()
    return any(keyword in text_low for keyword in CAR_KEYWORDS)


# ---------------------------------------------------------------------------
# 2. Resposta local (sem internet) para perguntas sobre o carro
# ---------------------------------------------------------------------------

def answer_car_question(text: str, snapshot: dict) -> str:
    """
    Gera uma resposta em português, em tom natural, usando os dados atuais
    do veículo. Não faz nenhuma chamada de rede — funciona mesmo sem
    internet ou GPS.
    """
    text_low = text.lower()

    rpm = snapshot.get("rpm")
    speed = snapshot.get("speed_kmh")
    temp = snapshot.get("engine_temp_c")
    fuel = snapshot.get("fuel_percent")
    battery = snapshot.get("battery_v")
    throttle = snapshot.get("throttle_percent")
    intake_temp = snapshot.get("intake_temp_c")
    engine_load = snapshot.get("engine_load_percent")
    maf = snapshot.get("maf_gs")
    o2_voltage = snapshot.get("o2_voltage_v")
    trim_short = snapshot.get("fuel_trim_short_percent")
    trim_long = snapshot.get("fuel_trim_long_percent")
    dtc_codes = snapshot.get("dtc_codes") or []
    mil_on = snapshot.get("mil_on")

    if "dtc" in text_low or "código de falha" in text_low or "codigo de falha" in text_low \
            or "falha" in text_low or "erro do motor" in text_low or "check engine" in text_low \
            or "luz de injeção" in text_low or "luz da injeção" in text_low:
        if not mil_on and not dtc_codes:
            return "Nenhuma luz de falha acesa e nenhum código de erro registrado no momento."
        if dtc_codes:
            codigos = "; ".join(dtc_codes)
            return f"A luz de injeção está acesa. Códigos encontrados: {codigos}."
        return "A luz de injeção está acesa, mas não consegui ler o código específico agora."

    if "carga do motor" in text_low:
        return f"A carga do motor está em {engine_load}%." if engine_load is not None else \
            "Não consegui ler a carga do motor agora."

    if "sonda" in text_low or " o2" in f" {text_low}":
        return f"A sonda lambda (O2) está lendo {o2_voltage}V." if o2_voltage is not None else \
            "Não consegui ler a sonda lambda agora."

    if "trim de combust" in text_low:
        if trim_short is None:
            return "Não consegui ler o ajuste de combustível agora."
        return f"O ajuste de combustível (fuel trim) está em {trim_short}% de curto prazo e {trim_long}% de longo prazo."

    if "fluxo de ar" in text_low or "maf" in text_low:
        return f"O fluxo de ar (MAF) está em {maf} g/s." if maf is not None else \
            "Não consegui ler o fluxo de ar agora."

    if "temperatura do ar" in text_low or "ar de admissão" in text_low:
        return f"A temperatura do ar de admissão está em {intake_temp}°C." if intake_temp is not None else \
            "Não consegui ler a temperatura do ar de admissão agora."

    if "rpm" in text_low:
        return f"O motor está a {rpm} RPM no momento." if rpm is not None else \
            "Não consegui ler o RPM agora. Verifique a conexão com o OBD2."

    if "veloc" in text_low or "km/h" in text_low:
        return f"Você está a {speed} km/h." if speed is not None else \
            "Não consegui ler a velocidade agora."

    if "temperatura" in text_low or "temp do motor" in text_low:
        if temp is None:
            return "Não consegui ler a temperatura do motor agora."
        aviso = " Está um pouco alta, fique de olho." if temp > 105 else ""
        return f"A temperatura do motor está em {temp}°C.{aviso}"

    if "combust" in text_low or "gasolina" in text_low or "tanque" in text_low:
        if fuel is None:
            return "Não consegui ler o nível de combustível agora."
        aviso = " Está baixo, considere abastecer em breve." if fuel < 15 else ""
        return f"Seu tanque está com {fuel}% de combustível.{aviso}"

    if "bateria" in text_low or "voltagem" in text_low:
        if battery is None:
            return "Não consegui ler a voltagem da bateria agora."
        aviso = " Isso está abaixo do normal, vale checar a bateria." if battery < 12.2 else ""
        return f"A bateria está em {battery} volts.{aviso}"

    if "acelera" in text_low:
        return f"O acelerador está em {throttle}% neste momento." if throttle is not None else \
            "Não consegui ler a posição do acelerador agora."

    # Pergunta genérica sobre "status do carro" -> manda um resumo
    partes = []
    if rpm is not None: partes.append(f"{rpm} RPM")
    if speed is not None: partes.append(f"{speed} km/h")
    if temp is not None: partes.append(f"motor a {temp}°C")
    if fuel is not None: partes.append(f"tanque em {fuel}%")
    if battery is not None: partes.append(f"bateria em {battery}V")
    if mil_on: partes.append("luz de injeção acesa")

    if partes:
        return "Status atual do carro: " + ", ".join(partes) + "."
    return "Não estou recebendo dados do OBD2 agora. Verifique se o adaptador está conectado."


# ---------------------------------------------------------------------------
# 3. Resposta via LLM (local com Ollama, ou nuvem com OpenAI) para perguntas gerais
# ---------------------------------------------------------------------------

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not OPENAI_AVAILABLE:
        return None

    if AI_PROVIDER == "local":
        # Ollama expõe uma API compatível com a da OpenAI, rodando local.
        # A "chave" aqui não é checada de verdade, só precisa não ser vazia.
        _client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama-local")
    elif OPENAI_API_KEY:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


SYSTEM_PROMPT = (
    "Você é o Eco, a inteligência artificial de bordo de um Ford EcoSport. "
    "Foi criado pelo Jonathas para ajudar e apoiar a família dele. "
    "Responda em português do Brasil, de forma natural, curta e objetiva "
    "(o motorista está ouvindo a resposta em voz, não lendo). "
    "Você NÃO tem acesso à internet em tempo real — se perguntarem sobre "
    "notícias, trânsito, previsão do tempo ou qualquer evento atual, diga "
    "claramente que não tem essa informação agora, em vez de inventar uma "
    "resposta. Evite respostas longas demais."
)


def answer_general_question(text: str) -> str:
    client = _get_client()
    if client is None:
        if AI_PROVIDER == "local":
            return ("Não consegui falar com o modelo local — o Ollama está "
                    "rodando? (veja o README para instalar)")
        return ("Ainda não consigo acessar a internet — falta configurar a "
                "chave da OpenAI no arquivo .env (OPENAI_API_KEY).")

    model = OLLAMA_MODEL if AI_PROVIDER == "local" else OPENAI_MODEL

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            max_tokens=150,
        )
        answer = (response.choices[0].message.content or "").strip()
        return answer or "Não consegui formular uma resposta agora."
    except Exception as e:
        logger.error(f"Erro ao consultar o modelo ({AI_PROVIDER}): {e}")
        if AI_PROVIDER == "local":
            return "Tive um problema para pensar nessa resposta agora. O Ollama está rodando?"
        return "Tive um problema para buscar essa informação na internet agora."


# ---------------------------------------------------------------------------
# 4. Função principal chamada pelo backend
# ---------------------------------------------------------------------------

def get_answer(text: str, snapshot: dict) -> dict:
    """
    Recebe a pergunta do usuário e o snapshot atual do carro.
    Retorna {"answer": str, "source": "local" | "internet"}

    Ordem de decisão:
      1. Conversa simples (oi, tudo bem, obrigado, tchau) -> resposta local
      2. Pergunta sobre DATA/HORA -> resposta local (relógio do PC)
      3. Pergunta sobre a FAMÍLIA (criador, esposa, filhas, avós) ->
         resposta fixa, local
      4. Pergunta sobre a FICHA TÉCNICA do carro (potência, câmbio,
         tanque, itens de série...) -> resposta fixa, local
      5. Pergunta sobre dado AO VIVO (RPM, velocidade, temperatura
         agora) -> resposta local usando o snapshot do OBD2
      6. Qualquer outra coisa -> Gemini (internet)
    """
    if small_talk.is_small_talk(text):
        return {"answer": small_talk.answer_small_talk(text), "source": "local"}
    if is_datetime_question(text):
        return {"answer": answer_datetime_question(text), "source": "local"}
    if family_info.is_family_question(text):
        return {"answer": family_info.answer_family_question(text), "source": "local"}
    if car_info.is_spec_question(text):
        return {"answer": car_info.answer_spec_question(text), "source": "local"}
    if is_car_question(text):
        return {"answer": answer_car_question(text, snapshot), "source": "local"}
    return {"answer": answer_general_question(text), "source": "internet"}
