# Vozes customizadas do C5

Aqui você pode colocar **seus próprios áudios gravados** pra frases
específicas do C5 — tipo os pacotes de voz do Waze. Quando a resposta do
C5 bater com uma dessas frases, ele toca o seu áudio em vez de gerar a
fala pelo TTS.

Importante: você só pode usar gravações suas, de alguém que autorizou, ou
de vozes livres de direitos autorais. Não é permitido usar a voz de
personagens ou atores sem autorização.

## Como adicionar uma voz customizada

1. Grave um áudio curto (recomendo `.mp3`, mas `.wav` também funciona) —
   pode ser você mesmo, um amigo, ou qualquer voz que você tenha o
   direito de usar.
2. Salve o arquivo dentro desta pasta: `voices/custom/`
   (ex: `voices/custom/boas_vindas.mp3`)
3. Abra o `voices/manifest.json` e edite (ou adicione) uma entrada:
   ```json
   {
     "id": "boas_vindas",
     "match": ["sistema c5 inicializado", "sou o c5"],
     "file": "boas_vindas.mp3"
   }
   ```
   - `match`: lista de trechos de texto (em minúsculas) que, se
     aparecerem na resposta do C5, fazem ele tocar esse áudio.
   - `file`: o nome exato do arquivo que você colocou em `voices/custom/`.
4. Salve o `manifest.json` e reinicia o app (`npm start`).

## O que pode ser customizado

Frases fixas funcionam bem (saudação, avisos de combustível baixo,
temperatura alta, bateria fraca). **Respostas com números variáveis**
(tipo "você está a 87 km/h", que muda toda vez) não dá pra pré-gravar —
essas continuam usando o TTS com o efeito de voz robótica.

Se quiser, pode ir adicionando mais frases fixas com o tempo — qualquer
coisa que o C5 fale sempre do mesmo jeito pode virar um áudio customizado.
