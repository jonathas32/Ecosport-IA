# Eco AI — IA de bordo local para o Ford EcoSport

Projeto irmão do C5 AI, adaptado para o **Ford EcoSport Titanium 2.0
16V manual, 2013**. Mesma arquitetura: leitura real do carro via OBD2
(Bluetooth, ELM327), funcionando 100% local — sem depender de internet
pros dados do veículo — e IA (Gemini) só pra perguntas gerais.

Como a EcoSport está com você, dá pra testar a conexão real do OBD2
direto nela.

## Estrutura do projeto
```
eco-ai/
├── Iniciar Eco.bat        ← duplo-clique pra abrir tudo
├── backend/
│   ├── obd_reader.py      ← leitura real do carro via Bluetooth
│   ├── ai_engine.py       ← decide: local vs. Gemini (internet)
│   ├── car_info.py        ← ficha técnica fixa do EcoSport Titanium 2013
│   ├── family_info.py     ← memória da família
│   ├── small_talk.py      ← conversas simples (oi, tudo bem, obrigado)
│   ├── app.py             ← servidor FastAPI (dados, chat, voz, transcrição)
│   ├── tts.py             ← texto → fala (edge-tts)
│   ├── stt.py             ← fala → texto (Whisper local)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── main.js            ← Electron, inicia o backend sozinho
│   ├── index.html
│   ├── style.css          ← identidade visual + múltiplos temas de cor
│   ├── sphere.js          ← esfera holográfica de partículas
│   ├── renderer.js
│   ├── voices/            ← vozes customizadas (opcional)
│   ├── assets/            ← coloque aqui seu ford-logo.png (ver abaixo)
│   └── package.json
└── .gitignore
```

## Sobre o logo da Ford
Não incluí o logo oficial da Ford no projeto — é uma marca registrada,
e não é algo que eu deva gerar. Se você quiser exibi-lo no rodapé do
app, salve sua própria imagem do logo como:
```
frontend/assets/ford-logo.png
```
O app já está preparado pra mostrar essa imagem automaticamente se o
arquivo existir (e simplesmente não aparece nada se você não colocar).

## Passo a passo de instalação

### 1. Backend (Python)
```powershell
cd backend
pip install -r requirements.txt
copy .env.example .env
```
Edite o `.env` com sua chave do Gemini (opcional, só pra perguntas
gerais) e ajuste `C5_FORCE_DEMO` (1 = modo demo, 0 = tenta conectar no
ELM327 de verdade).

### 2. Conectar o ELM327 na EcoSport
1. Ligue o ELM327 na porta OBD2 do carro (carro ligado ou pelo menos
   com a chave na posição II)
2. Pareia o Bluetooth no Windows (nome costuma ser "OBDII"), senha
   `1234` ou `0000`
3. Anota a porta COM criada (Configurações → Bluetooth → Mais opções →
   aba COM Ports)
4. Se não conectar automático, edite `OBD_PORT=COM5` (ajuste o número)
   no `.env`

### 3. Abrir o app
Duplo-clique em **`Iniciar Eco.bat`** — ele instala o resto sozinho na
primeira vez (Node/Electron) e já abre o app.

## O que pode perguntar
- Dados ao vivo: "qual a temperatura do motor?", "status do veículo",
  "tem algum código de falha?"
- Ficha técnica: "qual a potência do motor?", "quantos litros o
  tanque?", "conta a história do EcoSport"
- Família: "quem te criou?", "quem é a Luna?"
- Simples: "oi", "tudo bem?", "obrigado"
- Internet (Gemini): notícias, trânsito, previsão do tempo

## Créditos
Criado por Jonathas Benevides.
