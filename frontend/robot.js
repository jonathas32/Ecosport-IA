/* robot.js
 * O "rosto" do Eco: a imagem do robô (fundo removido), agora com
 * LIP-SYNC de verdade — 3 quadros da boca (fechada, meio aberta,
 * aberta) trocando enquanto ele fala, além de respirar/pulsar
 * reagindo ao RPM do carro.
 */

window.C5Orb = (function () {
  let wrap;
  let frames = {};
  let currentFrame = "closed";
  let rpmRatio = 0;
  let speaking = false;
  let talkLoopHandle = null;

  const MOUTH_FRAMES = ["closed", "mid", "open"];

  function init(el) {
    wrap = el;
    wrap.innerHTML = `
      <div class="robot-face-stack">
        <img src="assets/robot-mouth-closed.png" class="robot-face-img frame-closed active" alt="Eco" />
        <img src="assets/robot-mouth-mid.png" class="robot-face-img frame-mid" alt="" />
        <img src="assets/robot-mouth-open.png" class="robot-face-img frame-open" alt="" />
      </div>
    `;
    frames.closed = wrap.querySelector(".frame-closed");
    frames.mid = wrap.querySelector(".frame-mid");
    frames.open = wrap.querySelector(".frame-open");

    animate();
  }

  function showFrame(name) {
    if (name === currentFrame) return;
    currentFrame = name;
    MOUTH_FRAMES.forEach((f) => frames[f].classList.toggle("active", f === name));
  }

  function talkLoop() {
    if (!speaking) {
      showFrame("closed");
      talkLoopHandle = null;
      return;
    }
    // Escolhe o próximo quadro da boca de forma pseudo-aleatória, com
    // leve tendência a "fechada" de vez em quando (dá o efeito de sílaba)
    const roll = Math.random();
    const next = roll < 0.2 ? "closed" : roll < 0.6 ? "mid" : "open";
    showFrame(next);
    talkLoopHandle = setTimeout(talkLoop, 90 + Math.random() * 90);
  }

  function animate() {
    requestAnimationFrame(animate);
    if (!wrap) return;

    const t = performance.now() * 0.001;
    const breatheSpeed = speaking ? 5 : 1.1 + rpmRatio * 2.5;
    const breatheAmount = speaking ? 0.012 : 0.008 + rpmRatio * 0.02;
    const pulse = 1 + breatheAmount * Math.sin(t * breatheSpeed);

    const brightness = 1 + rpmRatio * 0.15;
    const stack = wrap.querySelector(".robot-face-stack");
    if (stack) {
      stack.style.transform = `scale(${pulse})`;
      stack.style.filter = `brightness(${brightness}) drop-shadow(0 0 22px rgba(var(--accent-rgb), 0.35))`;
    }
  }

  return {
    init,
    setRpm(rpm, maxRpm = 6500) {
      rpmRatio = Math.max(0, Math.min(1, rpm / maxRpm));
    },
    setSpeaking(isSpeaking) {
      speaking = isSpeaking;
      if (speaking && !talkLoopHandle) {
        talkLoop();
      } else if (!speaking) {
        showFrame("closed");
      }
    },
    setTheme() {
      // A imagem do robô mantém as cores originais; só o brilho ao
      // redor acompanha o tema, via CSS (--accent-rgb).
    },
  };
})();
