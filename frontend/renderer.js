/* renderer.js
 * Liga a interface ao backend local (FastAPI), que deve estar rodando em
 * http://127.0.0.1:8000 (rode "python app.py" na pasta backend/ antes de
 * abrir este app).
 */

const BACKEND_HTTP = "http://127.0.0.1:8000";
const BACKEND_WS = "ws://127.0.0.1:8000/ws/telemetry";

// ---------------------------------------------------------------------
// 0. Tela de abertura: toca o vídeo do robô, depois libera o app
// ---------------------------------------------------------------------
const splashScreen = document.getElementById("splashScreen");
const splashVideo = document.getElementById("splashVideo");
const skipSplashBtn = document.getElementById("skipSplashBtn");

function dismissSplash() {
  if (!splashScreen || splashScreen.classList.contains("fade-out")) return;
  splashScreen.classList.add("fade-out");
  setTimeout(() => splashScreen.remove(), 650);
}

if (splashVideo) {
  splashVideo.addEventListener("ended", dismissSplash);
  // Alguns navegadores/Electron bloqueiam autoplay com som; se falhar,
  // toca sem som em vez de travar a tela de abertura.
  splashVideo.play().catch(() => {
    splashVideo.muted = true;
    splashVideo.play().catch(() => dismissSplash());
  });
}
if (skipSplashBtn) {
  skipSplashBtn.addEventListener("click", dismissSplash);
}

// Contexto de áudio único, compartilhado pela voz do C5 e pela trilha de
// suspense do modo escuro
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

// ---------------------------------------------------------------------
// 1. Esfera holográfica (rosto do C5)
// ---------------------------------------------------------------------
const sphereCanvas = document.getElementById("sphereCanvas");
C5Orb.init(sphereCanvas);

// ---------------------------------------------------------------------
// 2. WebSocket: dados do carro em tempo real
// ---------------------------------------------------------------------
const obdDot = document.getElementById("obdDot");
const obdStatusText = document.getElementById("obdStatusText");
const coreRpmLabel = document.getElementById("coreRpmLabel");

function connectTelemetry() {
  const ws = new WebSocket(BACKEND_WS);

  ws.onopen = () => {
    obdStatusText.textContent = "Conectado ao backend local";
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateGauges(data);
  };

  ws.onclose = () => {
    obdDot.className = "dot offline";
    obdStatusText.textContent = "Backend desconectado. Tentando reconectar…";
    setTimeout(connectTelemetry, 2000);
  };

  ws.onerror = () => ws.close();
}

function updateGauges(data) {
  document.getElementById("g-speed").textContent = data.speed_kmh ?? "--";
  document.getElementById("g-temp").textContent = data.engine_temp_c ?? "--";
  document.getElementById("g-fuel").textContent = data.fuel_percent ?? "--";
  document.getElementById("g-throttle").textContent = data.throttle_percent ?? "--";
  document.getElementById("g-battery").textContent = data.battery_v ?? "--";
  document.getElementById("g-load").textContent = data.engine_load_percent ?? "--";
  document.getElementById("g-intake").textContent = data.intake_temp_c ?? "--";
  document.getElementById("g-maf").textContent = data.maf_gs ?? "--";
  document.getElementById("g-o2").textContent = data.o2_voltage_v ?? "--";

  const dtcEl = document.getElementById("g-dtc");
  const dtcWrap = document.getElementById("g-dtc-wrap");
  if (data.mil_on) {
    dtcEl.textContent = (data.dtc_codes && data.dtc_codes.length) ? data.dtc_codes.join(", ") : "Falha detectada";
    dtcWrap.classList.add("alert");
  } else {
    dtcEl.textContent = "OK";
    dtcWrap.classList.remove("alert");
  }

  coreRpmLabel.textContent = data.rpm ?? "—";
  C5Orb.setRpm(data.rpm || 0);

  if (data.connected) {
    obdDot.className = "dot connected";
    obdStatusText.textContent = "OBD2 conectado — dados reais do veículo";
  } else {
    obdDot.className = "dot demo";
    obdStatusText.textContent = "Modo demo (OBD2 não detectado)";
  }
}

connectTelemetry();

// ---------------------------------------------------------------------
// 3. Chat: enviar pergunta e mostrar resposta
// ---------------------------------------------------------------------
const chatLog = document.getElementById("chatLog");
const composerForm = document.getElementById("composerForm");
const textInput = document.getElementById("textInput");

function addMessage(text, who, sourceTag) {
  const div = document.createElement("div");
  div.className = `msg ${who}`;
  if (sourceTag) {
    const tag = document.createElement("span");
    tag.className = "source-tag";
    tag.textContent = sourceTag;
    div.appendChild(tag);
    div.appendChild(document.createElement("br"));
  }
  div.appendChild(document.createTextNode(text));
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

addMessage(
  "Sistema Eco inicializado. Olá, eu sou o Eco — a inteligência artificial de bordo do seu Ford EcoSport. " +
  "Leio direto do OBD2 os dados reais do carro (RPM, velocidade, temperatura do motor, combustível, " +
  "acelerador e bateria), sem precisar de internet pra isso. Também respondo perguntas gerais — " +
  "notícias, trânsito, previsão do tempo — usando a internet quando disponível. " +
  "Pode falar comigo digitando ou pelo microfone. Pergunte 'status do veículo' pra um resumo rápido.",
  "c5",
  "Eco"
);

async function askC5(text) {
  addMessage(text, "user");
  textInput.value = "";

  try {
    const res = await fetch(`${BACKEND_HTTP}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    const sourceTag = data.source === "local" ? "Dados do veículo · local" : "Internet";
    addMessage(data.answer, "c5", sourceTag);
    speak(data.answer);
  } catch (err) {
    addMessage("Não consegui falar com o backend. Ele está rodando (python app.py)?", "c5", "Erro");
  }
}

composerForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = textInput.value.trim();
  if (text) askC5(text);
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => askC5(chip.dataset.prompt));
});

// ---------------------------------------------------------------------
// 4. Voz: texto -> fala (custom, se existir) ou TTS + efeito robótico
// ---------------------------------------------------------------------
// Configurações de voz (persistem entre reinicializações do app)
let currentVoice = localStorage.getItem("c5_voice") || "pt-BR-AntonioNeural";
let robotEffectEnabled = localStorage.getItem("c5_robot") !== "false";

const settingsBtn = document.getElementById("settingsBtn");
const settingsPanel = document.getElementById("settingsPanel");
const voiceSelect = document.getElementById("voiceSelect");
const robotToggle = document.getElementById("robotToggle");
const testVoiceBtn = document.getElementById("testVoiceBtn");

voiceSelect.value = currentVoice;
robotToggle.checked = robotEffectEnabled;

settingsBtn.addEventListener("click", () => {
  settingsPanel.classList.toggle("open");
});

voiceSelect.addEventListener("change", () => {
  currentVoice = voiceSelect.value;
  localStorage.setItem("c5_voice", currentVoice);
});

robotToggle.addEventListener("change", () => {
  robotEffectEnabled = robotToggle.checked;
  localStorage.setItem("c5_robot", robotEffectEnabled);
});

// Tema: azul holográfico (padrão) ou escuro/roxo — com trilha de
// suspense original (sintetizada, sem nenhum áudio protegido) tocando
// baixinho quando o modo escuro está ativo.
const THEME_ACCENTS = {
  default: "#3ec9ff",
  green: "#39ff8f",
  white: "#5b3df5",
  "dark-purple": "#7a4fc4",
  red: "#ff3b3b",
  orange: "#ff8c32",
  yellow: "#ffd21f",
  cyan: "#22e6e6",
  pink: "#ff3ec9",
  indigo: "#6a5bff",
};

// Temas que usam a base escura genérica ("colored"), só trocando o
// tom de destaque — assim dá pra adicionar cor nova sem repetir CSS.
const GENERIC_COLOR_THEMES = ["red", "orange", "yellow", "cyan", "pink", "indigo"];

const themeBtn = document.getElementById("themeBtn");

// Ordem de ciclo: cada clique no botão passa pro próximo tema da lista.
const THEME_ORDER = [
  "default", "green", "cyan", "white", "yellow", "orange",
  "red", "pink", "indigo", "dark-purple", "gradient",
];
let currentTheme = localStorage.getItem("c5_theme") || "default";
let gradientLoopHandle = null;

function stopGradientLoop() {
  if (gradientLoopHandle) {
    clearInterval(gradientLoopHandle);
    gradientLoopHandle = null;
  }
}

function hueToHex(hue) {
  // Converte HSL pra hex sem precisar de biblioteca externa
  const s = 0.85, l = 0.55;
  const k = (n) => (n + hue / 30) % 12;
  const a = s * Math.min(l, 1 - l);
  const f = (n) => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  const toHex = (x) => Math.round(x * 255).toString(16).padStart(2, "0");
  return `#${toHex(f(0))}${toHex(f(8))}${toHex(f(4))}`;
}

function hexToRgbString(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `${r},${g},${b}`;
}

function applyTheme(themeName) {
  stopGradientLoop();
  themeBtn.classList.remove("active");

  if (themeName === "gradient") {
    document.documentElement.setAttribute("data-theme", "gradient");
    let hue = 0;
    gradientLoopHandle = setInterval(() => {
      hue = (hue + 2) % 360;
      const hex = hueToHex(hue);
      document.documentElement.style.setProperty("--accent", hex);
      document.documentElement.style.setProperty("--accent-rgb", hexToRgbString(hex));
      document.documentElement.style.setProperty("--accent-secondary", hueToHex((hue + 60) % 360));
      C5Orb.setTheme(hex);
    }, 60);
    themeBtn.classList.add("active");
    return;
  }

  if (GENERIC_COLOR_THEMES.includes(themeName)) {
    document.documentElement.setAttribute("data-theme", "colored");
    const accent = THEME_ACCENTS[themeName];
    const rgb = hexToRgbString(accent);
    document.documentElement.style.setProperty("--accent", accent);
    document.documentElement.style.setProperty("--accent-rgb", rgb);
    document.documentElement.style.setProperty("--accent-secondary", accent);
    document.documentElement.style.setProperty("--bg-glow-1", `rgba(${rgb}, 0.14)`);
    document.documentElement.style.setProperty("--bg-glow-2", `rgba(${rgb}, 0.08)`);
    C5Orb.setTheme(accent);
    themeBtn.classList.add("active");
    return;
  }

  document.documentElement.style.removeProperty("--accent");
  document.documentElement.style.removeProperty("--accent-rgb");
  document.documentElement.style.removeProperty("--accent-secondary");
  document.documentElement.style.removeProperty("--bg-glow-1");
  document.documentElement.style.removeProperty("--bg-glow-2");

  if (themeName === "default") {
    document.documentElement.removeAttribute("data-theme");
  } else {
    document.documentElement.setAttribute("data-theme", themeName);
  }

  const accent = THEME_ACCENTS[themeName] || THEME_ACCENTS.default;
  C5Orb.setTheme(accent);
  if (themeName !== "default") themeBtn.classList.add("active");
}

applyTheme(currentTheme);

themeBtn.addEventListener("click", () => {
  const idx = THEME_ORDER.indexOf(currentTheme);
  currentTheme = THEME_ORDER[(idx + 1) % THEME_ORDER.length];
  localStorage.setItem("c5_theme", currentTheme);
  applyTheme(currentTheme);
});

testVoiceBtn.addEventListener("click", () => {
  speakRaw("Olá, eu sou o Eco. Essa é a voz que você escolheu.");
});

// Manifesto de vozes customizadas (voices/manifest.json). Se o usuário
// gravou áudios próprios pra frases específicas, tocamos eles em vez do
// TTS. Ver voices/README.md para instruções de como adicionar.
let voiceManifest = null;

async function loadVoiceManifest() {
  try {
    const res = await fetch("voices/manifest.json");
    const data = await res.json();
    voiceManifest = data.entries || [];
  } catch (err) {
    voiceManifest = [];
    console.warn("Nenhum manifesto de voz customizada encontrado (ok, é opcional).");
  }
}
loadVoiceManifest();

function findCustomClip(text) {
  if (!voiceManifest) return null;
  const lower = text.toLowerCase();
  for (const entry of voiceManifest) {
    if (entry.match.some((phrase) => lower.includes(phrase.toLowerCase()))) {
      return entry.file;
    }
  }
  return null;
}

function makeDistortionCurve(amount) {
  const samples = 44100;
  const curve = new Float32Array(samples);
  for (let i = 0; i < samples; i++) {
    const x = (i * 2) / samples - 1;
    curve[i] = ((Math.PI + amount) * x) / (Math.PI + amount * Math.abs(x));
  }
  return curve;
}

// Gera e toca a fala pelo TTS, ignorando áudios customizados (usado pelo
// botão "Testar voz", que sempre quer ouvir o TTS puro com a config atual)
async function speakRaw(text) {
  try {
    const res = await fetch(`${BACKEND_HTTP}/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice: currentVoice }),
    });
    if (!res.ok) return;

    const arrayBuffer = await res.arrayBuffer();
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

    const source = audioCtx.createBufferSource();
    source.buffer = audioBuffer;

    if (robotEffectEnabled) {
      source.playbackRate.value = 0.86;

      const lowpass = audioCtx.createBiquadFilter();
      lowpass.type = "lowpass";
      lowpass.frequency.value = 3200;

      const distortion = audioCtx.createWaveShaper();
      distortion.curve = makeDistortionCurve(6);
      distortion.oversample = "2x";

      const ringGain = audioCtx.createGain();
      const ringOsc = audioCtx.createOscillator();
      ringOsc.frequency.value = 38;
      const ringDepth = audioCtx.createGain();
      ringDepth.gain.value = 0.15;
      ringOsc.connect(ringDepth);
      ringDepth.connect(ringGain.gain);
      ringGain.gain.value = 1;
      ringOsc.start();

      source.connect(lowpass);
      lowpass.connect(distortion);
      distortion.connect(ringGain);
      ringGain.connect(audioCtx.destination);

      source.onended = () => {
        C5Orb.setSpeaking(false);
        ringOsc.stop();
        resumeWakeAfterSpeech();
      };
    } else {
      source.connect(audioCtx.destination);
      source.onended = () => {
        C5Orb.setSpeaking(false);
        resumeWakeAfterSpeech();
      };
    }

    pauseWakeForSpeech();
    C5Orb.setSpeaking(true);
    source.start();
  } catch (err) {
    console.warn("TTS indisponível:", err);
  }
}

async function speak(text) {
  // 1. Prioridade: áudio customizado gravado pelo usuário, se existir
  const customFile = findCustomClip(text);
  if (customFile) {
    try {
      const audio = new Audio(`voices/custom/${customFile}`);
      C5Orb.setSpeaking(true);
      audio.onended = () => C5Orb.setSpeaking(false);
      await audio.play();
      return;
    } catch (err) {
      console.warn("Não consegui tocar o áudio customizado, caindo para TTS:", err);
    }
  }

  // 2. Sem áudio customizado: gera a fala pelo backend com a voz/efeito
  //    escolhidos nas configurações
  await speakRaw(text);
}

// ---------------------------------------------------------------------
// 5. Microfone: grava áudio de verdade e manda pro backend transcrever
//    (Whisper local). NÃO usamos o SpeechRecognition do navegador porque
//    ele não funciona dentro do Electron — o Google bloqueia esse
//    serviço fora do Chrome de verdade, retornando sempre "network error".
// ---------------------------------------------------------------------
const micBtn = document.getElementById("micBtn");
let micStream = null;
let mediaRecorder = null;
let isRecording = false;

async function getMicStream() {
  if (micStream) return micStream;
  micStream = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
      channelCount: 1,
    },
  });
  return micStream;
}

// Bitrate mais alto pra não perder qualidade da fala na compressão
// (o padrão do navegador costuma ser baixo demais pra reconhecimento
// de voz com boa precisão)
const RECORDER_OPTIONS = { audioBitsPerSecond: 128000 };

async function transcribeBlob(blob) {
  const form = new FormData();
  form.append("audio", blob, "gravacao.webm");
  const res = await fetch(`${BACKEND_HTTP}/transcribe`, { method: "POST", body: form });
  if (!res.ok) throw new Error("Falha na transcrição");
  const data = await res.json();
  return (data.text || "").trim();
}

async function recordFor(milliseconds) {
  // Grava por um período fixo e devolve o Blob resultante. Usado tanto
  // pelo botão de microfone (push-to-talk) quanto pela escuta contínua.
  const stream = await getMicStream();
  const recorder = new MediaRecorder(stream, RECORDER_OPTIONS);
  const chunks = [];
  recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };

  return new Promise((resolve) => {
    recorder.onstop = () => resolve(new Blob(chunks, { type: "audio/webm" }));
    recorder.start();
    setTimeout(() => {
      if (recorder.state !== "inactive") recorder.stop();
    }, milliseconds);
  });
}

if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
  micBtn.addEventListener("click", async () => {
    if (isRecording) {
      // Clique enquanto grava = parar antes do tempo e já transcrever
      if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
      return;
    }
    try {
      isRecording = true;
      micBtn.classList.add("listening");
      const stream = await getMicStream();
      const chunks = [];
      mediaRecorder = new MediaRecorder(stream, RECORDER_OPTIONS);
      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
      mediaRecorder.onstop = async () => {
        isRecording = false;
        micBtn.classList.remove("listening");
        const blob = new Blob(chunks, { type: "audio/webm" });
        try {
          const text = await transcribeBlob(blob);
          if (text) askC5(text);
        } catch (err) {
          console.warn("Erro ao transcrever:", err);
        }
      };
      mediaRecorder.start();
      // Grava no máximo 8 segundos automaticamente, caso o usuário
      // esqueça de clicar de novo pra parar
      setTimeout(() => {
        if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
      }, 8000);
    } catch (err) {
      isRecording = false;
      micBtn.classList.remove("listening");
      console.warn("Não consegui acessar o microfone:", err);
    }
  });
} else {
  micBtn.disabled = true;
  micBtn.title = "Microfone não disponível neste ambiente";
}

// ---------------------------------------------------------------------
// 6. Ativação por voz contínua ("C5", estilo Alexa)
// ---------------------------------------------------------------------
// Como não temos reconhecimento de voz em tempo real (ver seção 5), a
// escuta contínua funciona gravando em blocos curtos (alguns segundos)
// e transcrevendo cada bloco localmente, procurando a palavra "C5".
// Isso tem um pequeno atraso (o tamanho do bloco) comparado a um
// assistente tipo Alexa de verdade, mas funciona 100% offline.
const WAKE_WORDS = ["eco", "ico", "êco", "hico", "ei eco", "oi eco", "ok eco", "ei ico", "oi ico"];
const WAKE_CHUNK_MS = 3500;
const COMMAND_CHUNK_MS = 5500; // mais tempo pra capturar frases maiores

const wakeStatusRow = document.getElementById("wakeStatusRow");
const wakeDot = document.getElementById("wakeDot");
const wakeStatusText = document.getElementById("wakeStatusText");

let wakeEnabled = localStorage.getItem("c5_wakeword") === "true";
let wakeShouldRun = false;
let wakePaused = false;
let awaitingCommand = false;

function extractCommandAfterWakeWord(transcript) {
  const lower = transcript.toLowerCase();
  for (const w of WAKE_WORDS) {
    const idx = lower.indexOf(w);
    if (idx === -1) continue;

    let rest = transcript.slice(idx + w.length);

    // Limpa pontuação/espaços soltos e remove repetições da própria
    // palavra de ativação (ex: "eco, eco, eco." -> ""), pra não tratar
    // isso como se fosse um comando de verdade.
    let changed = true;
    while (changed) {
      changed = false;
      rest = rest.replace(/^[\s,.\-!?]+/, "");
      for (const w2 of WAKE_WORDS) {
        if (rest.toLowerCase().startsWith(w2)) {
          rest = rest.slice(w2.length);
          changed = true;
        }
      }
    }

    return rest.trim();
  }
  return null;
}

function setWakeUI(state) {
  if (state === "active") {
    wakeDot.classList.add("active");
    wakeStatusText.textContent = "Pode falar…";
  } else {
    wakeDot.classList.remove("active");
    wakeStatusText.textContent = 'Aguardando "Eco"…';
  }
}

async function wakeListenLoop() {
  while (wakeShouldRun) {
    if (wakePaused) {
      await new Promise((r) => setTimeout(r, 300));
      continue;
    }
    try {
      // Enquanto só está esperando ouvir "Eco", grava blocos curtos (mais
      // responsivo). Depois que ouviu a palavra, grava um bloco mais
      // longo pro comando de verdade, pra não cortar frases maiores.
      const chunkDuration = awaitingCommand ? COMMAND_CHUNK_MS : WAKE_CHUNK_MS;
      const blob = await recordFor(chunkDuration);
      if (!wakeShouldRun) break;
      const transcript = await transcribeBlob(blob);
      console.log('[Eco escuta] ouvi:', JSON.stringify(transcript));
      if (!transcript) continue;

      if (awaitingCommand) {
        awaitingCommand = false;
        setWakeUI("idle");
        askC5(transcript);
        continue;
      }

      const command = extractCommandAfterWakeWord(transcript);
      if (command !== null) {
        if (command.length > 0) {
          askC5(command);
        } else {
          awaitingCommand = true;
          setWakeUI("active");
        }
      }
    } catch (err) {
      console.warn("Erro na escuta contínua:", err);
      await new Promise((r) => setTimeout(r, 1000));
    }
  }
}

function startWakeListening() {
  wakeShouldRun = true;
  wakeStatusRow.style.display = "flex";
  setWakeUI("idle");
  wakeListenLoop();
}

function stopWakeListening() {
  wakeShouldRun = false;
  wakeStatusRow.style.display = "none";
}

// Pausa a escuta contínua enquanto o C5 fala (evita ele se ouvir) e
// retoma logo depois
function pauseWakeForSpeech() {
  wakePaused = true;
}
function resumeWakeAfterSpeech() {
  setTimeout(() => { wakePaused = false; }, 400);
}

const wakeWordToggle = document.getElementById("wakeWordToggle");
wakeWordToggle.checked = wakeEnabled;
if (wakeEnabled) startWakeListening();

wakeWordToggle.addEventListener("change", () => {
  wakeEnabled = wakeWordToggle.checked;
  localStorage.setItem("c5_wakeword", wakeEnabled);
  if (wakeEnabled) {
    startWakeListening();
  } else {
    stopWakeListening();
  }
});
