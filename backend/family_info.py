"""
family_info.py
--------------
Memória fixa sobre quem o C5 serve e apoia: o Jonathas (criador) e sua
família. Assim, se alguém perguntar "quem te criou?", "quem é o
Jonathas?" ou similar, o C5 já sabe responder, sem precisar de internet.
"""

FAMILY_PROFILE = {
    "criador": "Jonathas",
    "esposa": "Jordania",
    "filhas": ["Luna", "Lara"],
    "avo_materna": "Dona Ana",
    "avo_materno": "Nivaldo",
}

FAMILY_KEYWORDS = {
    "criador": ["jonathas", "seu criador", "te criou", "te fez", "te programou", "criou você"],
    "esposa": ["jordania", "esposa", "jojo"],
    "luna": ["luna"],
    "lara": ["lara"],
    "avos": ["dona ana", "nivaldo", "sabará", "sabara", "avó", "avo", "avô"],
    "familia_geral": ["família", "familia"],
    "sobre_c5": ["o que é o eco", "oque é o eco", "quem é você", "quem é o eco", "o que você é", "o que você faz"],
}


def is_family_question(text: str) -> bool:
    text_low = text.lower()
    return any(
        any(kw in text_low for kw in keywords)
        for keywords in FAMILY_KEYWORDS.values()
    )


def answer_family_question(text: str) -> str:
    text_low = text.lower()
    f = FAMILY_PROFILE

    if any(kw in text_low for kw in FAMILY_KEYWORDS["sobre_c5"]):
        return (
            f"Eu sou o Eco, a inteligência artificial de bordo, criado pelo {f['criador']} "
            f"pra ajudar e apoiar a família dele no dia a dia. Cuido dos dados do carro e "
            f"também posso responder outras perguntas."
        )

    if any(kw in text_low for kw in FAMILY_KEYWORDS["luna"]):
        return f"A Luna é filha do {f['criador']}."

    if any(kw in text_low for kw in FAMILY_KEYWORDS["lara"]):
        return f"A Lara é filha do {f['criador']}."

    if any(kw in text_low for kw in FAMILY_KEYWORDS["esposa"]):
        return f"A esposa do {f['criador']} é a {f['esposa']}."

    if any(kw in text_low for kw in FAMILY_KEYWORDS["avos"]):
        return f"A avó é a {f['avo_materna']}, mãe da {f['esposa']}. O avô é o {f['avo_materno']}."

    if any(kw in text_low for kw in FAMILY_KEYWORDS["criador"]):
        return (
            f"Fui criado pelo {f['criador']}. Estou aqui pra ajudar e apoiar ele e a "
            f"família dele no dia a dia."
        )

    if any(kw in text_low for kw in FAMILY_KEYWORDS["familia_geral"]):
        filhas = " e ".join(f["filhas"])
        return (
            f"Fui criado pelo {f['criador']} pra apoiar a família dele: a esposa "
            f"{f['esposa']}, as filhas {filhas}, e o apoio da avó {f['avo_materna']} "
            f"e do avô {f['avo_materno']}."
        )

    return "Sou o Eco, criado pelo Jonathas pra ajudar e apoiar a família dele."
