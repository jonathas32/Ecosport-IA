/* robot.js
 * O "rosto" do Eco: a imagem do robô (fundo removido), com uma leve
 * respiração/pulso reagindo ao RPM, e um brilho na região da boca que
 * pulsa enquanto o Eco está falando — uma aproximação simples de "boca
 * mexendo", já que trabalhamos com uma imagem estática (não é lip-sync
 * de verdade quadro a quadro, mas dá a sensação de estar "vivo" falando).
 */

window.C5Orb = (function () {
  let wrap, img, mouthGlow;
  let rpmRatio = 0;
  let speaking = false;

  function init(el) {
    wrap = el;
    wrap.innerHTML = `
      <img src="assets/robot-face.png" class="robot-face-img" id="robotFaceImg" alt="Eco" />
      <div class="mouth-glow" id="mouthGlow"></div>
    `;
    img = wrap.querySelector(".robot-face-img");
    mouthGlow = wrap.querySelector(".mouth-glow");
    animate();
  }

  function animate() {
    requestAnimationFrame(animate);
    if (!img) return;

    const t = performance.now() * 0.001;
    const breatheSpeed = speaking ? 5 : 1.1 + rpmRatio * 2.5;
    const breatheAmount = speaking ? 0.015 : 0.008 + rpmRatio * 0.02;
    const pulse = 1 + breatheAmount * Math.sin(t * breatheSpeed);
    img.style.transform = `scale(${pulse})`;

    const brightness = 1 + rpmRatio * 0.15;
    img.style.filter = `brightness(${brightness}) drop-shadow(0 0 22px rgba(var(--accent-rgb), 0.35))`;

    if (mouthGlow) {
      mouthGlow.classList.toggle("active", speaking);
    }
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
      // A imagem do robô não muda de cor com o tema (mantém as cores
      // originais dele); só o brilho ao redor acompanha o tema, via CSS.
    },
  };
})();
