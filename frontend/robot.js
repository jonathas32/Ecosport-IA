/* robot.js
 * O "rosto" do Eco: um vídeo do robô em loop contínuo, com o fundo verde
 * removido EM TEMPO REAL (quadro a quadro, via canvas) — assim ele fica
 * sempre em movimento, sem precisar de nenhum codec especial de vídeo
 * com transparência.
 */

window.C5Orb = (function () {
  let wrap, video, canvas, ctx;
  let rpmRatio = 0;
  let speaking = false;
  let ready = false;

  // Cor aproximada do fundo verde do vídeo (ajustada pra esse material
  // específico). Se um dia trocar o vídeo por outro com um verde
  // diferente, é só ajustar esses valores.
  const KEY_R = 42, KEY_G = 155, KEY_B = 54;
  const THRESHOLD = 70; // quão parecido com o verde precisa ser pra virar transparente
  const SOFT_EDGE = 40; // faixa de transição suave (anti-serrilhado)

  function init(el) {
    wrap = el;
    wrap.innerHTML = `
      <video id="robotIdleVideo" src="assets/robot-idle.mp4" autoplay loop muted playsinline style="display:none;"></video>
      <canvas class="robot-canvas" id="robotCanvas"></canvas>
    `;
    video = wrap.querySelector("#robotIdleVideo");
    canvas = wrap.querySelector(".robot-canvas");
    ctx = canvas.getContext("2d", { willReadFrequently: true });

    video.addEventListener("loadedmetadata", () => {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ready = true;
    });
    video.play().catch(() => {});

    renderLoop();
    animate();
  }

  function renderLoop() {
    requestAnimationFrame(renderLoop);
    if (!ready || video.paused || video.ended) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const frame = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = frame.data;

    for (let i = 0; i < data.length; i += 4) {
      const r = data[i], g = data[i + 1], b = data[i + 2];
      const dist = Math.sqrt((r - KEY_R) ** 2 + (g - KEY_G) ** 2 + (b - KEY_B) ** 2);
      if (dist < THRESHOLD) {
        data[i + 3] = 0;
      } else if (dist < THRESHOLD + SOFT_EDGE) {
        data[i + 3] = ((dist - THRESHOLD) / SOFT_EDGE) * 255;
      }
    }
    ctx.putImageData(frame, 0, 0);
  }

  function animate() {
    requestAnimationFrame(animate);
    if (!canvas) return;

    // Reage ao RPM: vídeo um pouco mais rápido e brilhante em giros altos
    if (video) {
      video.playbackRate = 1 + rpmRatio * 0.3 + (speaking ? 0.15 : 0);
    }
    const brightness = 1 + rpmRatio * 0.15 + (speaking ? 0.1 : 0);
    canvas.style.filter = `brightness(${brightness}) drop-shadow(0 0 24px rgba(var(--accent-rgb), 0.3))`;
  }

  return {
    init,
    setRpm(rpm, maxRpm = 6500) {
      rpmRatio = Math.max(0, Math.min(1, rpm / maxRpm));
    },
    setSpeaking(isSpeaking) {
      speaking = isSpeaking;
    },
    setTheme() {
      // O vídeo mantém as cores originais; só o brilho ao redor
      // acompanha o tema, via CSS (--accent-rgb).
    },
  };
})();
