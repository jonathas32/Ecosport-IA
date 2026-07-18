"""
small_talk.py
--------------
Respostas locais e instantâneas para conversas simples do dia a dia
(cumprimentos, agradecimentos, despedidas). Sem isso, mensagens como "oi"
ou "obrigado" cairiam desnecessariamente pro Gemini (internet), o que é
lento e sem necessidade pra algo tão simples.
"""

import re
import random

GREETINGS = [r"\boi\b", r"\bolá\b", r"\bola\b", r"\be ai\b", r"\beae\b",
             r"\bbom dia\b", r"\bboa tarde\b", r"\bboa noite\b", r"\bopa\b"]

WELLBEING = [r"\btudo bem\b", r"\bcomo vai\b", r"\bcomo você está\b",
             r"\bcomo voce esta\b", r"\bbeleza\b", r"\bcomo você tá\b"]

THANKS = [r"\bobrigad[ao]\b", r"\bvaleu\b", r"\bvlw\b", r"\bagradeç"]

FAREWELL = [r"\btchau\b", r"\bfalou\b", r"\baté mais\b", r"\bate mais\b",
            r"\bflw\b", r"\baté logo\b", r"\bate logo\b"]

GREETING_REPLIES = [
    "Oi! Como posso ajudar?",
    "Olá! Tudo certo por aqui. O que você precisa?",
    "Oi! Pode perguntar sobre o carro ou qualquer outra coisa.",
]

WELLBEING_REPLIES = [
    "Tudo certo por aqui, sistemas funcionando normalmente. E com você?",
    "Tudo em ordem! Pronto pra ajudar no que precisar.",
]

THANKS_REPLIES = [
    "De nada! Qualquer coisa é só chamar.",
    "Por nada! Estou aqui pra isso.",
]

FAREWELL_REPLIES = [
    "Até mais! Dirija com cuidado.",
    "Falou! Qualquer coisa é só me chamar de novo.",
]


def _matches(patterns, text_low):
    return any(re.search(p, text_low) for p in patterns)


def is_small_talk(text: str) -> bool:
    text_low = text.lower()
    return (
        _matches(GREETINGS, text_low)
        or _matches(WELLBEING, text_low)
        or _matches(THANKS, text_low)
        or _matches(FAREWELL, text_low)
    )


def answer_small_talk(text: str) -> str:
    text_low = text.lower()

    if _matches(THANKS, text_low):
        return random.choice(THANKS_REPLIES)
    if _matches(FAREWELL, text_low):
        return random.choice(FAREWELL_REPLIES)
    if _matches(WELLBEING, text_low):
        return random.choice(WELLBEING_REPLIES)
    if _matches(GREETINGS, text_low):
        return random.choice(GREETING_REPLIES)

    return "Oi! Como posso ajudar?"
