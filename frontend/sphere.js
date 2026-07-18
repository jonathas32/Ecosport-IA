/* sphere.js
 * O "cérebro" holográfico do C5: uma esfera de partículas conectadas por
 * linhas finas, girando devagar, com pulsos de "dados" viajando pelas
 * conexões — como se estivesse sempre pensando/recebendo informação.
 * Feito em Canvas 2D puro (sem depender de nenhuma biblioteca externa),
 * projeção 3D simples (perspectiva).
 */

window.C5Orb = (function () {
  let canvas, ctx;
  let width = 0, height = 0, dpr = 1;
  let points = [];
  let edges = [];
  let outerParticles = [];
  let pulses = [];
  let rotY = 0, rotX = 0;
  let rpmRatio = 0;
  let speaking = false;
  let accentColor = { r: 62, g: 201, b: 255 }; // azul-ciano (tema padrão)

  const SPHERE_RADIUS = 100;
  const POINT_COUNT = 90;
  const CAMERA_DIST = 320;

  function fibonacciSphere(samples) {
    const pts = [];
    const phi = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < samples; i++) {
      const y = 1 - (i / (samples - 1)) * 2;
      const radiusAtY = Math.sqrt(Math.max(0, 1 - y * y));
      const theta = phi * i;
      const x = Math.cos(theta) * radiusAtY;
      const z = Math.sin(theta) * radiusAtY;
      pts.push({ x0: x * SPHERE_RADIUS, y0: y * SPHERE_RADIUS, z0: z * SPHERE_RADIUS });
    }
    return pts;
  }

  function buildEdges(pts) {
    const result = [];
    const threshold = SPHERE_RADIUS * 0.55;
    for (let i = 0; i < pts.length; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        const dx = pts[i].x0 - pts[j].x0;
        const dy = pts[i].y0 - pts[j].y0;
        const dz = pts[i].z0 - pts[j].z0;
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (dist < threshold) result.push([i, j]);
      }
    }
    return result;
  }

  function buildOuterParticles(count) {
    const arr = [];
    for (let i = 0; i < count; i++) {
      const r = SPHERE_RADIUS * (1.3 + Math.random() * 0.6);
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      arr.push({
        x0: r * Math.sin(phi) * Math.cos(theta),
        y0: r * Math.sin(phi) * Math.sin(theta),
        z0: r * Math.cos(phi),
        driftSeed: Math.random() * 1000,
        connectTo: Math.floor(Math.random() * POINT_COUNT),
      });
    }
    return arr;
  }

  function resize() {
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    width = rect.width;
    height = rect.height;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function project(p) {
    // Rotaciona em Y e depois em X
    const cosY = Math.cos(rotY), sinY = Math.sin(rotY);
    let x = p.x0 * cosY - p.z0 * sinY;
    let z = p.x0 * sinY + p.z0 * cosY;
    let y = p.y0;

    const cosX = Math.cos(rotX), sinX = Math.sin(rotX);
    const y2 = y * cosX - z * sinX;
    const z2 = y * sinX + z * cosX;

    const scale = CAMERA_DIST / (CAMERA_DIST + z2);
    const cx = width / 2;
    const cy = height / 2;
    const px = cx + x * scale * (width / 320);
    const py = cy + y2 * scale * (width / 320);
    return { px, py, z: z2, scale };
  }

  function colorStr(alpha) {
    return `rgba(${accentColor.r},${accentColor.g},${accentColor.b},${alpha})`;
  }

  function spawnPulseIfDue() {
    const chance = 0.02 + rpmRatio * 0.05 + (speaking ? 0.08 : 0);
    if (Math.random() < chance && edges.length) {
      const [a, b] = edges[Math.floor(Math.random() * edges.length)];
      pulses.push({ a, b, t: 0, speed: 0.03 + Math.random() * 0.02 });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);

    const projected = points.map(project);
    const projectedOuter = outerParticles.map((p) => {
      const t = performance.now() * 0.0002 + p.driftSeed;
      const drift = 4 * Math.sin(t);
      return project({ x0: p.x0 + drift, y0: p.y0, z0: p.z0 });
    });

    // Linhas de conexão da esfera
    ctx.lineWidth = 1;
    edges.forEach(([i, j]) => {
      const a = projected[i], b = projected[j];
      const depthAvg = (a.z + b.z) / 2;
      const alpha = Math.max(0.04, Math.min(0.35, 0.22 + depthAvg / 400));
      ctx.strokeStyle = colorStr(alpha);
      ctx.beginPath();
      ctx.moveTo(a.px, a.py);
      ctx.lineTo(b.px, b.py);
      ctx.stroke();
    });

    // Pulsos de dados viajando pelas conexões
    pulses.forEach((pulse) => {
      const a = projected[pulse.a], b = projected[pulse.b];
      const x = a.px + (b.px - a.px) * pulse.t;
      const y = a.py + (b.py - a.py) * pulse.t;
      ctx.beginPath();
      ctx.arc(x, y, 2.2, 0, Math.PI * 2);
      ctx.fillStyle = colorStr(0.95);
      ctx.shadowColor = colorStr(1);
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.shadowBlur = 0;
      pulse.t += pulse.speed;
    });
    pulses = pulses.filter((p) => p.t < 1);

    // Nós (pontos) da esfera
    projected.forEach((p) => {
      const size = Math.max(0.8, 2.2 * p.scale);
      const alpha = Math.max(0.25, Math.min(1, 0.5 + p.z / 200));
      ctx.beginPath();
      ctx.arc(p.px, p.py, size, 0, Math.PI * 2);
      ctx.fillStyle = colorStr(alpha);
      ctx.shadowColor = colorStr(0.9);
      ctx.shadowBlur = 6 + rpmRatio * 8;
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    // Partículas externas flutuando (com linha fina de conexão)
    projectedOuter.forEach((p, idx) => {
      const target = projected[outerParticles[idx].connectTo];
      ctx.strokeStyle = colorStr(0.12);
      ctx.beginPath();
      ctx.moveTo(p.px, p.py);
      ctx.lineTo(target.px, target.py);
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(p.px, p.py, 2, 0, Math.PI * 2);
      ctx.fillStyle = colorStr(0.8);
      ctx.shadowColor = colorStr(0.8);
      ctx.shadowBlur = 6;
      ctx.fill();
      ctx.shadowBlur = 0;
    });
  }

  function animate() {
    requestAnimationFrame(animate);
    if (!ctx) return;

    const rotSpeed = 0.0025 + rpmRatio * 0.006 + (speaking ? 0.004 : 0);
    rotY += rotSpeed;
    rotX = Math.sin(performance.now() * 0.0002) * 0.15;

    spawnPulseIfDue();
    draw();
  }

  function init(el) {
    canvas = el;
    ctx = canvas.getContext("2d");
    points = fibonacciSphere(POINT_COUNT);
    edges = buildEdges(points);
    outerParticles = buildOuterParticles(10);

    window.addEventListener("resize", resize);
    resize();
    animate();
  }

  return {
    init,
    setRpm(rpm, maxRpm = 6500) {
      rpmRatio = Math.max(0, Math.min(1, rpm / maxRpm));
    },
    setSpeaking(isSpeaking) {
      speaking = isSpeaking;
    },
    setTheme(hexColor) {
      const r = parseInt(hexColor.slice(1, 3), 16);
      const g = parseInt(hexColor.slice(3, 5), 16);
      const b = parseInt(hexColor.slice(5, 7), 16);
      accentColor = { r, g, b };
    },
  };
})();
