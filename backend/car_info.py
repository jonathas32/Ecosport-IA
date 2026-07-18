"""
car_info.py
-----------
Informações FIXAS sobre o modelo do carro (não mudam com o tempo, ao
contrário dos dados do OBD2 que mudam a cada segundo). Isso é a "memória"
do Eco sobre o próprio veículo — ficha técnica completa do Ford EcoSport
Titanium 2.0 16V manual, ano 2013 (dados oficiais da Ford Brasil).
"""

CAR_PROFILE = {
    "modelo": "Ford EcoSport Titanium 2.0 16V manual",
    "ano": "2013",
    "geracao": "segunda geração, lançada no Brasil em 2012, com identidade visual alinhada ao Fusion e plataforma compartilhada com o Fiesta",

    # Motor
    "motor": "Duratec 2.0, 4 cilindros em linha, 16V, 1.999 cm³, flex (etanol/gasolina)",
    "potencia": "cerca de 147 cv com etanol e 141 cv com gasolina",
    "torque": "19,7 kgfm / 193,3 Nm a 4.250 rpm (etanol)",
    "rotacao_maxima": "6.700 rpm",
    "relacao_compressao": "10,8:1",

    # Câmbio
    "cambio": "manual de 5 marchas, tração dianteira",

    # Desempenho
    "aceleracao_0_100": "cerca de 10,5 segundos (com etanol)",

    # Consumo
    "consumo_cidade": "6 km/l com etanol e 8,5 km/l com gasolina",
    "consumo_estrada": "7,2 km/l com etanol e 10,5 km/l com gasolina",
    "capacidade_tanque": "52 litros",
    "autonomia_estimada": "até cerca de 546 km com gasolina na estrada",

    # Dimensões
    "comprimento": "4,241 m",
    "largura": "1,765 m sem os espelhos (2,057 m com espelhos)",
    "altura": "cerca de 1,70 m",
    "entre_eixos": "2,521 m",
    "altura_solo": "200 mm (bem alta pra categoria)",
    "porta_malas": "362 litros (até 705 litros com o banco traseiro rebatido)",
    "peso": "cerca de 1.228 kg em ordem de marcha",
    "carga_util": "cerca de 448 kg",

    # Mecânica / chassi
    "tracao": "dianteira",
    "direcao": "elétrica, tipo pinhão e cremalheira",
    "freios": "sistema hidráulico com ABS e EBD (freio a disco nas rodas dianteiras)",
    "suspensao": (
        "dianteira independente; traseira Multilink, com braços de controle, "
        "molas helicoidais, amortecedores e barra estabilizadora de 20 mm"
    ),

    # Segurança
    "seguranca": [
        "airbags frontais (duplo)",
        "ABS com EBD",
        "controle de estabilidade e tração",
        "fixação ISOFIX para cadeirinhas infantis",
    ],

    # Equipamentos de série (Titanium)
    "itens_serie": [
        "ar-condicionado digital",
        "bancos revestidos em couro",
        "chave presencial",
        "volante multifuncional com ajuste de altura",
        "computador de bordo",
        "faróis de neblina",
        "rodas de liga leve",
        "sensores de estacionamento",
        "sistema multimídia SYNC com Bluetooth e USB",
        "vidros elétricos nas quatro portas",
        "travas elétricas",
        "desembaçador do vidro traseiro",
        "direção elétrica",
        "alarme",
    ],

    # Curiosidades / história
    "curiosidades": [
        "O EcoSport nasceu no Brasil em 2003, sendo um dos poucos projetos de carro concebidos e desenvolvidos aqui",
        "Essa segunda geração (2012) foi a primeira a ser vendida também fora do Brasil, incluindo Europa e Ásia",
        "Compartilha a plataforma com o Ford Fiesta e o motor Duratec com o Fiesta e o Focus",
        "O motor 2.0 também esteve disponível com câmbio automático Powershift de dupla embreagem",
        "A versão 4WD (tração nas 4 rodas) chegou meses depois do lançamento nacional",
    ],
}


# Palavras-chave que indicam uma pergunta sobre a FICHA TÉCNICA do carro
# (fixa, não muda), em vez de uma leitura AO VIVO do OBD2.
SPEC_KEYWORDS = {
    "potencia": ["potência", "quantos cavalos", "cv do motor", "hp"],
    "torque": ["torque"],
    "motor_info": ["que motor é esse", "duratec", "cilindrada"],
    "cambio": ["câmbio", "marchas", "transmissão"],
    "aceleracao_0_100": ["0 a 100", "0-100", "aceleração"],
    "consumo": ["consumo médio", "quantos km por litro", "km/l"],
    "capacidade_tanque": ["capacidade do tanque", "quantos litros o tanque", "tanque cheio"],
    "porta_malas": ["porta-malas", "porta malas", "bagageiro"],
    "dimensoes": ["comprimento", "largura do carro", "altura do carro", "entre-eixos", "entre eixos", "dimensões", "altura do solo", "altura livre do solo"],
    "peso": ["peso do carro", "quanto pesa", "carga útil"],
    "suspensao": ["suspensão"],
    "freios": ["freio", "abs", "ebd"],
    "seguranca": ["segurança do carro", "airbag", "controle de tração", "quantos airbags", "isofix"],
    "itens_serie": ["itens de série", "o que vem de série", "equipamentos do carro", "acessórios de série"],
    "historia": ["história do ecosport", "historia do ecosport", "quando surgiu", "curiosidade"],
    "modelo_ano": ["que carro é esse", "qual o modelo", "que ano é o carro", "ano do carro", "modelo do meu carro"],
}


def is_spec_question(text: str) -> bool:
    text_low = text.lower()
    return any(
        any(kw in text_low for kw in keywords)
        for keywords in SPEC_KEYWORDS.values()
    )


def answer_spec_question(text: str) -> str:
    text_low = text.lower()
    p = CAR_PROFILE

    if any(kw in text_low for kw in SPEC_KEYWORDS["potencia"]):
        return f"O motor do seu {p['modelo']} entrega {p['potencia']}, com {p['torque']} de torque."

    if any(kw in text_low for kw in SPEC_KEYWORDS["torque"]):
        return f"O torque do motor é de {p['torque']}."

    if any(kw in text_low for kw in SPEC_KEYWORDS["motor_info"]):
        return f"O motor é o {p['motor']}, com rotação máxima de {p['rotacao_maxima']}."

    if any(kw in text_low for kw in SPEC_KEYWORDS["cambio"]):
        return f"Seu carro tem câmbio {p['cambio']}."

    if any(kw in text_low for kw in SPEC_KEYWORDS["aceleracao_0_100"]):
        return f"O 0 a 100 km/h leva {p['aceleracao_0_100']}."

    if any(kw in text_low for kw in SPEC_KEYWORDS["consumo"]):
        return f"O consumo médio de fábrica é {p['consumo_cidade']} na cidade e {p['consumo_estrada']} na estrada."

    if any(kw in text_low for kw in SPEC_KEYWORDS["capacidade_tanque"]):
        return f"O tanque tem capacidade de {p['capacidade_tanque']}, dando uma autonomia estimada de {p['autonomia_estimada']}."

    if any(kw in text_low for kw in SPEC_KEYWORDS["porta_malas"]):
        return f"O porta-malas tem {p['porta_malas']}."

    if any(kw in text_low for kw in SPEC_KEYWORDS["dimensoes"]):
        return (
            f"O carro tem {p['comprimento']} de comprimento, {p['largura']}, "
            f"{p['altura']} de altura, {p['entre_eixos']} de entre-eixos, e {p['altura_solo']} de altura livre do solo."
        )

    if any(kw in text_low for kw in SPEC_KEYWORDS["peso"]):
        return f"O carro pesa {p['peso']} em ordem de marcha, com carga útil de {p['carga_util']}."

    if any(kw in text_low for kw in SPEC_KEYWORDS["suspensao"]):
        return f"A suspensão é {p['suspensao']}."

    if any(kw in text_low for kw in SPEC_KEYWORDS["freios"]):
        return f"Os freios são: {p['freios']}."

    if any(kw in text_low for kw in SPEC_KEYWORDS["seguranca"]):
        itens = ", ".join(p["seguranca"])
        return f"Em segurança, o carro conta com: {itens}."

    if any(kw in text_low for kw in SPEC_KEYWORDS["itens_serie"]):
        itens = ", ".join(p["itens_serie"])
        return f"De série, o {p['modelo']} vem com: {itens}."

    if any(kw in text_low for kw in SPEC_KEYWORDS["historia"]):
        curiosidades = " ".join(p["curiosidades"])
        return f"{p['geracao']}. {curiosidades}"

    if any(kw in text_low for kw in SPEC_KEYWORDS["modelo_ano"]):
        return f"Você está no seu {p['modelo']}, ano {p['ano']}."

    # fallback: resumo geral
    return (
        f"Você está no {p['modelo']} ({p['ano']}), motor {p['motor']}, "
        f"{p['potencia']} de potência, câmbio {p['cambio']}."
    )
