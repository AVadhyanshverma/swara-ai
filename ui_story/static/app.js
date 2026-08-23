/* ══════════════════════════════════════════════════════════════════════
   SWARA — cinematic scroll engine
   Single-ticker architecture:  GSAP ticker → Lenis → ScrollTrigger →
   simulation (frame-rate-independent damping) → render.
   ════════════════════════════════════════════════════════════════════ */

import * as THREE from 'https://unpkg.com/three@0.158.0/build/three.module.js';

/* ── 1 · MATH ──────────────────────────────────────────────────────── */
const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
const lerp  = (a, b, t) => a + (b - a) * t;
/* Exponential damping — identical feel at 60Hz, 120Hz or 30Hz. */
const damp  = (a, b, lambda, dt) => lerp(a, b, 1 - Math.exp(-lambda * dt));

/* Heavier-than-standard eases (functions, so no premium plugins needed) */
const easeOutHeavy   = p => (p === 1 ? 1 : 1 - Math.pow(2, -11 * p));
const easeInHeavy    = p => p * p * p;
const easeInOutHeavy = p => (p < 0.5 ? 8 * p ** 4 : 1 - Math.pow(-2 * p + 2, 4) / 2);

/* ── 2 · QUALITY TIERS ─────────────────────────────────────────────── */
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const coarse  = matchMedia('(pointer: coarse)').matches;
const cores   = navigator.hardwareConcurrency || 4;
const params  = new URLSearchParams(location.search);

const TIERS = {
  high: { particles: 200000, dust: 2400, dpr: 1.75, bloom: false,  blur: 1 },
  mid:  { particles: 95000,  dust: 1200, dpr: 1.5,  bloom: false, blur: 1 },
  low:  { particles: 35000,  dust: 500,  dpr: 1.25, bloom: false, blur: 0 },
  cpu:  { particles: 5000,   dust: 100,  dpr: 0.75, bloom: false, blur: 0 },
};

let tier = 'high';
if (coarse || innerWidth < 900 || cores <= 4) tier = 'mid';
if (reduced || cores <= 2 || innerWidth < 520) tier = 'low';
if (TIERS[params.get('q')]) tier = params.get('q');

const Q = TIERS[tier];
document.body.classList.add('tier-' + tier);

/* ── 3 · RENDERER / SCENE ──────────────────────────────────────────── */
const canvas = document.querySelector('#webgl-canvas');
let renderer = null;

try {
  renderer = new THREE.WebGLRenderer({
    canvas, antialias: tier === 'high', alpha: false,
    powerPreference: 'high-performance', stencil: false, depth: true,
  });
  renderer.setSize(innerWidth, innerHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio, Q.dpr));
  renderer.setClearColor(0x0b0b0f, 1);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
} catch (e) {
  document.body.classList.add('no-webgl');
  console.warn('[SWARA] WebGL unavailable — running DOM-only.', e);
}

const scene  = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.1, 400);
camera.position.set(0, 34, 118);

/* Uniforms live outside the WebGL guard so GSAP can always tween them. */
const U = {
  uTime:          { value: 0 },
  uFlow:          { value: 0 },      // accumulated distance — never teleports
  uScroll:        { value: 0 },
  uMorph:         { value: 0 },
  uVelocity:      { value: 0 },
  uPixelRatio:    { value: renderer ? renderer.getPixelRatio() : 1 },
  uMouseStrength: { value: 0 },
  uSpotBase:      { value: coarse ? 0.55 : 0.32 },
  uMouseWorld:    { value: new THREE.Vector3() },
  uMouseSmooth:   { value: new THREE.Vector2(0.5, 0.5) },
  uSphereOffset:  { value: new THREE.Vector3(35, 0, 0) },
  uResolution:    { value: new THREE.Vector2(innerWidth, innerHeight) },
};

/* ── 4 · GEOMETRY ──────────────────────────────────────────────────── */
const COUNT = Q.particles;
const PLANE_Z = 250;

function buildWater() {
  const g = new THREE.BufferGeometry();
  const pos     = new Float32Array(COUNT * 3);
  const sphere  = new Float32Array(COUNT * 3);
  const colors  = new Float32Array(COUNT * 3);
  const randoms = new Float32Array(COUNT);

  const cAccent = new THREE.Color('#7fff00');
  const cMid    = new THREE.Color('#1a4a0a');
  const cDark   = new THREE.Color('#020d04');

  for (let i = 0; i < COUNT; i++) {
    const i3 = i * 3;
    const x = (Math.random() - 0.5) * 140;
    const z = (Math.random() - 0.5) * PLANE_Z;

    pos[i3] = x; pos[i3 + 1] = 0; pos[i3 + 2] = z;
    randoms[i] = Math.random();

    /* colour: deep in the trough, neon at the banks */
    const dist = Math.abs(x) / 70;
    const c = Math.random() < 0.7
      ? cDark.clone().lerp(cMid, dist + Math.random() * 0.15)
      : cMid.clone().lerp(cAccent, dist * 0.6 + Math.random() * 0.3);
    colors[i3] = c.r; colors[i3 + 1] = c.g; colors[i3 + 2] = c.b;

    /* sphere destination — 6% become an orbiting halo ring */
    if (Math.random() > 0.94) {
      const a = Math.random() * Math.PI * 2;
      const r = 15.5 + Math.random() * 2.2;
      sphere[i3]     = Math.cos(a) * r;
      sphere[i3 + 1] = (Math.random() - 0.5) * 1.1;
      sphere[i3 + 2] = Math.sin(a) * r;
    } else {
      const phi   = Math.acos(-1 + (2 * i) / COUNT);
      const theta = Math.sqrt(COUNT * Math.PI) * phi;
      const r = 10;
      sphere[i3]     = r * Math.cos(theta) * Math.sin(phi);
      sphere[i3 + 1] = r * Math.sin(theta) * Math.sin(phi);
      sphere[i3 + 2] = r * Math.cos(phi);
    }
  }

  g.setAttribute('position',       new THREE.BufferAttribute(pos, 3));
  g.setAttribute('spherePosition', new THREE.BufferAttribute(sphere, 3));
  g.setAttribute('customColor',    new THREE.BufferAttribute(colors, 3));
  g.setAttribute('aRandom',        new THREE.BufferAttribute(randoms, 1));
  return g;
}

const VERT = /* glsl */ `
  uniform float uTime, uFlow, uMorph, uVelocity, uPixelRatio, uMouseStrength;
  uniform vec3  uMouseWorld, uSphereOffset;

  attribute vec3  spherePosition, customColor;
  attribute float aRandom;

  varying vec3  vColor;
  varying float vWave, vDepth, vMorph;

  const float PLANE_Z = 250.0;

  float hash11(float p){
    p = fract(p * 0.1031); p *= p + 33.33; p *= p + p; return fract(p);
  }

  /* Gerstner wave helper — returns (horizontal displacement, vertical displacement) */
  vec2 gerstner(vec2 pos, vec2 dir, float steepness, float waveLen, float speed) {
    float k = 6.28318 / waveLen;
    float c = speed / k;
    float a = steepness / k;
    float phase = k * (dot(dir, pos) - c * uTime);
    return vec2(dir.x * a * cos(phase), a * sin(phase));
  }

  void main() {
    vColor = customColor;
    vec3 pos = position;

    /* Endless flow. uFlow is integrated on the CPU (flow += dt * speed),
       so changing speed can never teleport a particle. */
    pos.z = mod(pos.z - uFlow + PLANE_Z * 0.5, PLANE_Z) - PLANE_Z * 0.5;

    /* Valley  \___/  — pow() guarded so it never sees a negative base */
    float valley = pow(max(abs(pos.x) - 18.0, 0.0), 1.3) * 0.12;

    /* ── Gerstner water: subtle, cinematic waves ────────────────── */
    float chop = 1.0 + uVelocity * 0.15;

    /* 4 Gerstner wave layers — gentle amplitudes for a flat, elegant surface */
    vec2 g1 = gerstner(pos.xz, normalize(vec2(1.0, 0.3)),  0.08 * chop, 42.0, 3.0);
    vec2 g2 = gerstner(pos.xz, normalize(vec2(-0.6, 1.0)), 0.06 * chop, 28.0, 2.4);
    vec2 g3 = gerstner(pos.xz, normalize(vec2(0.4, -0.8)), 0.05 * chop, 18.0, 3.6);
    vec2 g4 = gerstner(pos.xz, normalize(vec2(-1.0, 0.2)), 0.03 * chop, 12.0, 4.5);

    /* Horizontal displacement — subtle orbital motion */
    pos.x += (g1.x + g2.x + g3.x + g4.x) * 0.6;
    pos.z += (g1.x * 0.3 + g2.x * 0.8 + g3.x * (-0.6) + g4.x * 0.2) * 0.6;

    /* Vertical — the main wave height, kept low */
    float wave = g1.y * 2.8 + g2.y * 2.2 + g3.y * 1.4 + g4.y * 0.8;

    /* Fine detail octaves (capillary ripples) */
    wave += sin((pos.x * 1.3 + pos.z * 1.6) * 0.25 - uTime * 1.80) * 0.35 * chop;
    wave += cos((pos.x * -1.0 + pos.z * 1.2) * 0.35 + uTime * 2.20) * 0.22;
    wave += sin((pos.x * 2.5 - pos.z * 2.0) * 0.50 + uTime * 3.00) * 0.10;
    wave += sin((pos.x * 4.0 + pos.z * 3.5) * 0.70 - uTime * 4.50) * 0.05;

    /* Per-particle jitter — very subtle turbulence */
    wave += (sin(aRandom * 6.28 + uTime * 2.0) * 0.12 +
             cos(aRandom * 12.57 + uTime * 3.1) * 0.06);

    /* Pointer bulge + trailing ripple, both faded by pointer energy */
    float dM     = distance(pos.xz, uMouseWorld.xz);
    float bulge  = smoothstep(16.0, 0.0, dM) * 3.5 * uMouseStrength;
    float ripple = sin(dM * 0.55 - uTime * 2.4) *
                   smoothstep(24.0, 3.0, dM) * 0.7 * uMouseStrength;

    /* Concentric ring waves from cursor */
    float ringWave = sin(dM * 0.9 - uTime * 4.0) *
                     smoothstep(32.0, 5.0, dM) * 0.25 * uMouseStrength;

    vec3 waterPos = pos;
    waterPos.y += valley + wave + bulge + ripple + ringWave;

    /* ── Sphere target ────────────────────────────────────────── */
    vec3  sPos   = spherePosition;
    float isRing = step(13.0, length(spherePosition));

    float spin = uTime * mix(0.22, 0.55, isRing);
    float ss = sin(spin), sc = cos(spin);
    sPos.xz = vec2(sPos.x * sc - sPos.z * ss, sPos.x * ss + sPos.z * sc);

    float sNoise = sin(sPos.x * 0.6 + uTime * 1.4) *
                   cos(sPos.y * 0.7 + uTime * 1.1) * 1.15;
    sPos += normalize(sPos + 1e-4) * sNoise * (1.0 - isRing * 0.75);

    vec3 centre = vec3(0.0, 5.0, -85.0) + uSphereOffset;
    centre.y += sin(uTime * 0.55) * 0.7;
    sPos += centre;

    /* ── Manhole vortex ───────────────────────────────────────── */
    if (uMorph > 0.001) {
      float dV = distance(waterPos.xz, centre.xz) + 0.1;
      float sw = uMorph * 25.0 / (dV * 0.05 + 1.0);
      float sws = sin(sw), swc = cos(sw);
      vec2 o = waterPos.xz - centre.xz;
      waterPos.xz = vec2(o.x * swc - o.y * sws, o.x * sws + o.y * swc) + centre.xz;
      waterPos.y -= uMorph * 40.0 / (dV * 0.06 + 1.0);
      waterPos.xz = mix(waterPos.xz, centre.xz, uMorph * 0.3);
    }

    /* ── Staggered morph on a Bézier arc ──────────────────────── */
    float seed    = hash11(aRandom * 91.7 + 3.1);
    float stagger = seed * 0.42;
    float local   = clamp((uMorph - stagger) / 0.58, 0.0, 1.0);
    float curve   = local * local * (3.0 - 2.0 * local);
    curve         = curve * curve * (3.0 - 2.0 * curve);   // double smooth = weight

    vec3 arcDir = normalize(vec3(
      hash11(seed * 13.0) - 0.5,
      abs(hash11(seed * 29.0) - 0.5) + 0.45,
      hash11(seed * 47.0) - 0.5) + 1e-4);

    vec3 mid = mix(waterPos, sPos, 0.5) + arcDir * (6.0 + seed * 15.0);
    vec3 a   = mix(waterPos, mid,  curve);
    vec3 b   = mix(mid,      sPos, curve);
    vec3 finalPos = mix(a, b, curve);

    vec4 mv = modelViewMatrix * vec4(finalPos, 1.0);
    vWave  = wave + bulge;
    vDepth = length(mv.xyz);
    vMorph = curve;

    /* Size must respect DPR or retina renders everything half-scale */
    float size = mix(105.0, 152.0, curve) * (0.72 + seed * 0.56);
    gl_PointSize = clamp(size * uPixelRatio / max(-mv.z, 0.001),
                         uPixelRatio, 13.0 * uPixelRatio);
    gl_Position = projectionMatrix * mv;
  }
`;

const FRAG = /* glsl */ `
  precision highp float;
  uniform vec2  uResolution, uMouseSmooth;
  uniform float uMorph, uSpotBase;
  varying vec3  vColor;
  varying float vWave, vDepth, vMorph;

  void main() {
    float d = length(gl_PointCoord - 0.5);
    if (d > 0.5) discard;

    float core  = smoothstep(0.50, 0.06, d);
    float halo  = smoothstep(0.50, 0.00, d) * 0.35;
    float shape = core + halo;

    float aspect = uResolution.x / uResolution.y;
    vec2 sp = gl_FragCoord.xy / uResolution;  sp.x *= aspect;
    vec2 mp = uMouseSmooth;                   mp.x *= aspect;
    float md = distance(sp, mp);

    float radius = uSpotBase + uMorph * 0.75;
    float spot   = smoothstep(radius, radius * 0.22, md);
    spot = max(spot, smoothstep(0.25, 0.85, uMorph));

    float glow  = smoothstep(0.14, 0.0, md) * 1.15;
    float fog   = smoothstep(12.0, 62.0, vDepth);
    float crest = smoothstep(1.8, 5.2, vWave) * 0.55;

    vec3 col = vColor + vec3(crest * 0.25, crest * 0.85, crest * 0.12);
    col += vec3(glow * 0.18, glow * 0.50, glow * 0.06);
    col  = mix(col, col * vec3(1.15, 1.38, 0.85) + vec3(0.01, 0.09, 0.0), vMorph * 0.85);

    float alpha = max(shape * spot * (1.0 - fog * 0.85), 0.006);
    gl_FragColor = vec4(col, alpha);
  }
`;

let water = null, dust = null;

if (renderer) {
  water = new THREE.Points(buildWater(), new THREE.ShaderMaterial({
    uniforms: U, vertexShader: VERT, fragmentShader: FRAG,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  }));
  water.frustumCulled = false;
  scene.add(water);

  /* Soft round sprite for dust + horizon glow */
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const cx = c.getContext('2d');
  const grad = cx.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, 'rgba(255,255,255,1)');
  grad.addColorStop(0.35, 'rgba(255,255,255,0.45)');
  grad.addColorStop(1, 'rgba(255,255,255,0)');
  cx.fillStyle = grad; cx.fillRect(0, 0, 64, 64);
  const sprite = new THREE.CanvasTexture(c);

  const dg = new THREE.BufferGeometry();
  const dp = new Float32Array(Q.dust * 3);
  for (let i = 0; i < Q.dust; i++) {
    dp[i * 3]     = (Math.random() - 0.5) * 130;
    dp[i * 3 + 1] = (Math.random() - 0.5) * 52 + 8;
    dp[i * 3 + 2] = (Math.random() - 0.5) * 190;
  }
  dg.setAttribute('position', new THREE.BufferAttribute(dp, 3));
  dust = new THREE.Points(dg, new THREE.PointsMaterial({
    color: '#7fff00', size: 0.62, map: sprite, transparent: true,
    opacity: 0.2, depthWrite: false, blending: THREE.AdditiveBlending,
  }));
  scene.add(dust);

  /* Atmospheric horizon glow — cheap depth cue at the vanishing point */
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({
    map: sprite, color: 0x2e7a10, transparent: true,
    opacity: 0.5, depthWrite: false, blending: THREE.AdditiveBlending,
  }));
  glow.position.set(0, 4, -118);
  glow.scale.set(180, 90, 1);
  scene.add(glow);
}

/* ── 5 · POST-PROCESSING (dynamically imported, fails soft) ────────── */
let composer = null, finalPass = null;

async function initPost() {
  if (!renderer || !Q.bloom) return;
  try {
    const [
      { EffectComposer }, { RenderPass }, { UnrealBloomPass },
      { ShaderPass }, { OutputPass },
    ] = await Promise.all([
      import('https://unpkg.com/three@0.158.0/examples/jsm/postprocessing/EffectComposer.js'),
      import('https://unpkg.com/three@0.158.0/examples/jsm/postprocessing/RenderPass.js'),
      import('https://unpkg.com/three@0.158.0/examples/jsm/postprocessing/UnrealBloomPass.js'),
      import('https://unpkg.com/three@0.158.0/examples/jsm/postprocessing/ShaderPass.js'),
      import('https://unpkg.com/three@0.158.0/examples/jsm/postprocessing/OutputPass.js'),
    ]);

    composer = new EffectComposer(renderer);
    composer.setPixelRatio(renderer.getPixelRatio());
    composer.setSize(innerWidth, innerHeight);
    composer.addPass(new RenderPass(scene, camera));
    composer.addPass(new UnrealBloomPass(
      new THREE.Vector2(innerWidth, innerHeight), 0.62, 0.75, 0.16));
    composer.addPass(new OutputPass());

    finalPass = new ShaderPass({
      uniforms: {
        tDiffuse:     { value: null },
        uTime:        { value: 0 },
        uAberration:  { value: 0 },
      },
      vertexShader: `varying vec2 vUv; void main(){ vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
      fragmentShader: `
        uniform sampler2D tDiffuse; uniform float uTime, uAberration;
        varying vec2 vUv;
        void main(){
          vec2 dir = vUv - 0.5;
          float d  = length(dir);
          float amt = uAberration * (0.0016 + d * 0.0075);
          vec3 col = vec3(
            texture2D(tDiffuse, vUv - dir * amt).r,
            texture2D(tDiffuse, vUv).g,
            texture2D(tDiffuse, vUv + dir * amt).b);
          float n = fract(sin(dot(vUv * 900.0 + uTime, vec2(12.9898, 78.233))) * 43758.5453);
          col += (n - 0.5) * 0.022;
          gl_FragColor = vec4(col, 1.0);
        }`,
    });
    composer.addPass(finalPass);
  } catch (err) {
    composer = null;
    console.warn('[SWARA] post-processing skipped', err);
  }
}
const postPromise = initPost().then(() => {
  if (renderer && scene && camera) {
    renderer.compile(scene, camera);
    if (composer) composer.render();
  }
});

/* ── 6 · TEXT SPLITTING (masked reveals, <br> safe) ────────────────── */
function split(el, mode) {
  if (el.__split) return el.__split;
  const out = [];
  const frag = document.createDocumentFragment();

  Array.from(el.childNodes).forEach(node => {
    if (node.nodeType !== 3) { frag.appendChild(node.cloneNode(true)); return; }
    const units = mode === 'chars'
      ? node.textContent.split('')
      : node.textContent.split(/(\s+)/);

    units.forEach(u => {
      if (!u.trim()) { frag.appendChild(document.createTextNode(u)); return; }
      const mask  = document.createElement('span'); mask.className = 'mask';
      const inner = document.createElement('span'); inner.className = 'mask-i';
      inner.textContent = u;
      mask.appendChild(inner); frag.appendChild(mask); out.push(inner);
    });
  });

  el.textContent = '';
  el.appendChild(frag);
  el.__split = out;
  return out;
}
const splitAll = sel =>
  [...document.querySelectorAll(sel)].flatMap(el => split(el, el.dataset.split));

document.querySelectorAll('[data-split]').forEach(el => split(el, el.dataset.split));

/* ── 7 · SMOOTH SCROLL + SCROLLTRIGGER ─────────────────────────────── */
gsap.registerPlugin(ScrollTrigger);
ScrollTrigger.config({ ignoreMobileResize: true });

const LenisCtor = window.Lenis?.default || window.Lenis;
let lenis = null;

if (LenisCtor && !reduced) {
  lenis = new LenisCtor({
    lerp: 0.075,              // the core of the "heavy glide"
    wheelMultiplier: 0.88,
    touchMultiplier: 1.35,
    smoothWheel: true,
    syncTouch: false,
  });
  lenis.on('scroll', ScrollTrigger.update);
  lenis.stop();               // held until the intro reveal releases it
}

/* ── 8 · MASTER SCRUBBED TIMELINE ──────────────────────────────────── */
const B = Q.blur;                                   // blur budget (0 on low tier)
const blurPx = px => `blur(${px * B}px)`;

const camTarget  = { x: 0, y: 12, z: 80 };
const lookTarget = { x: 0, y: 0,  z: -25 };
const sphereOff  = U.uSphereOffset.value;

gsap.set('.intro-section',  { opacity: 0, scale: 1.045 });
gsap.set('.data-section',   { opacity: 1 });
gsap.set('.data-point',     { opacity: 0, y: 70, filter: blurPx(10) });
gsap.set('.sphere-right-text, .sphere-left-text', { opacity: 0 });
gsap.set('.final-section',  { opacity: 0, scale: 0.88, filter: blurPx(12) });
gsap.set(splitAll('.sphere-heading, .sphere-subtext, .final-section .title'),
         { yPercent: 112, opacity: 0 });

let progress = 0, rawVelocity = 0;

const tl = gsap.timeline({
  scrollTrigger: {
    trigger: '.scroll-container',
    start: 'top top',
    end: 'bottom bottom',
    scrub: 1.4,                       // real smoothing lives in Lenis + damping
    invalidateOnRefresh: true,
    onUpdate: self => { progress = self.progress; rawVelocity = self.getVelocity(); },
  },
});

/* Camera — targets only; the actual camera chases them with damping. */
tl.to(camTarget,  { z: -46, y: 6.5, duration: 0.70, ease: 'none' }, 0)
  .to(camTarget,  { z: -70, y: 5.0, duration: 0.30, ease: easeInHeavy }, 0.70)
  .to(lookTarget, { y: 2.2, duration: 1.00, ease: 'none' }, 0);

/* Intro out */
tl.to('.intro-section',
      { opacity: 0, scale: 0.94, y: -46, filter: blurPx(14),
        duration: 0.12, ease: 'power2.in' }, 0.05);

/* Data in / out */
tl.to('.data-point',
      { opacity: 1, y: 0, filter: blurPx(0),
        stagger: 0.045, duration: 0.15, ease: easeOutHeavy }, 0.22)
  .to('.data-section',
      { opacity: 0, y: -46, filter: blurPx(14),
        duration: 0.12, ease: 'power2.in' }, 0.46);

/* Scroll-driven counters */
document.querySelectorAll('[data-count]').forEach((el, i) => {
  const to   = parseFloat(el.dataset.count);
  const from = parseFloat(el.dataset.from ?? '0');
  const sfx  = el.dataset.suffix ?? '';
  const o = { v: from };
  el.textContent = Math.round(from) + sfx;
  tl.to(o, {
    v: to, duration: 0.12, ease: easeOutHeavy,
    onUpdate: () => { el.textContent = Math.round(o.v) + sfx; },
  }, 0.24 + i * 0.02);
});

/* ── Sphere journey ──
   GAP: data counters finish ~0.38, data fades at 0.46 (done by 0.58).
   Morph begins at 0.60 — a clear breathing pause before the ball forms. */
tl.to(U.uMorph, { value: 1, duration: 0.18, ease: 'power2.inOut' }, 0.60);

/* 1 · arrives right */
tl.to(sphereOff, { x: 26, y: -2, z: 15, duration: 0.10, ease: easeOutHeavy }, 0.62);

/* 2 · holds right, copy reveals left */
tl.to('.sphere-right-text', { opacity: 1, duration: 0.045 }, 0.69)
  .to(split(document.querySelector('.sphere-right-text .sphere-heading'), 'words'),
      { yPercent: 0, opacity: 1, stagger: 0.014, duration: 0.05, ease: easeOutHeavy }, 0.693)
  .to(split(document.querySelector('.sphere-right-text .sphere-subtext'), 'words'),
      { yPercent: 0, opacity: 1, stagger: 0.006, duration: 0.04, ease: easeOutHeavy }, 0.72)
  .to('.sphere-right-text',
      { opacity: 0, filter: blurPx(10), duration: 0.04, ease: 'power2.in' }, 0.78);

/* 3 · heavy sweep left */
tl.to(sphereOff, { x: -26, y: -2, z: 15, duration: 0.09, ease: easeInOutHeavy }, 0.80);

/* 4 · holds left, copy reveals right */
tl.to('.sphere-left-text', { opacity: 1, duration: 0.045 }, 0.86)
  .to(split(document.querySelector('.sphere-left-text .sphere-heading'), 'words'),
      { yPercent: 0, opacity: 1, stagger: 0.014, duration: 0.05, ease: easeOutHeavy }, 0.863)
  .to(split(document.querySelector('.sphere-left-text .sphere-subtext'), 'words'),
      { yPercent: 0, opacity: 1, stagger: 0.006, duration: 0.04, ease: easeOutHeavy }, 0.885)
  .to('.sphere-left-text',
      { opacity: 0, filter: blurPx(10), duration: 0.04, ease: 'power2.in' }, 0.92);

/* 5 · settles centre — the heaviest deceleration of the whole page */
tl.to(sphereOff, { x: 0, y: 0, z: 0, duration: 0.07, ease: easeOutHeavy }, 0.94);

/* Finale */
tl.to('.final-section',
      { opacity: 1, scale: 1, filter: blurPx(0), duration: 0.05, ease: 'power2.out' }, 0.955)
  .to(splitAll('.final-section .title'),
      { yPercent: 0, opacity: 1, stagger: 0.02, duration: 0.04, ease: easeOutHeavy }, 0.965);

/* ── 9 · HUD ───────────────────────────────────────────────────────── */
const CHAPTERS = [
  [0.00, 'ORIGIN'], [0.22, 'METRICS'], [0.60, 'AUTONOMY'],
  [0.80, 'ZERO TRUST'], [0.94, 'ARRIVAL'],
];
const $status  = document.getElementById('hud-status');
const $chapter = document.getElementById('chapter-name');
const $num     = document.getElementById('chapter-num');
const $pct     = document.getElementById('scroll-pct');
const setFill  = gsap.quickSetter('#progress-fill', 'scaleX');

let chapterIdx = 0;
function setChapter(i) {
  if (i === chapterIdx) return;
  chapterIdx = i;
  gsap.timeline()
    .to($chapter, { opacity: 0, y: -7, filter: blurPx(5), duration: 0.26, ease: 'power2.in' })
    .add(() => {
      $chapter.textContent = CHAPTERS[i][1];
      $num.textContent = String(i + 1).padStart(2, '0');
    })
    .fromTo($chapter, { y: 7 },
      { opacity: 1, y: 0, filter: blurPx(0), duration: 0.5, ease: easeOutHeavy });
}

let statusText = '';
function setStatus(t) {
  if (t === statusText) return;
  statusText = t;
  gsap.timeline()
    .to($status, { opacity: 0, duration: 0.25, ease: 'power2.in' })
    .add(() => { $status.textContent = t; })
    .to($status, { opacity: 1, duration: 0.5, ease: 'power2.out' });
}

/* ── 10 · POINTER ──────────────────────────────────────────────────── */
const raycaster = new THREE.Raycaster();
const ndc   = new THREE.Vector2();
const floor = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
const hit   = new THREE.Vector3();

let mx = 0, my = 0, msx = 0.5, msy = 0.5, pointerEnergy = 0, moving = 0;

function onPointer(cx, cy) {
  mx = (cx / innerWidth) * 2 - 1;
  my = -(cy / innerHeight) * 2 + 1;
  msx = cx / innerWidth;
  msy = 1 - cy / innerHeight;
  moving = 1;

  ndc.set(mx, my);
  raycaster.setFromCamera(ndc, camera);
  if (raycaster.ray.intersectPlane(floor, hit)) U.uMouseWorld.value.copy(hit);
}

addEventListener('pointermove', e => {
  onPointer(e.clientX, e.clientY);
  if (e.pointerType === 'mouse') {
    document.body.classList.add('cursor-ready');
    ringX(e.clientX); ringY(e.clientY);
    dotX(e.clientX);  dotY(e.clientY);
  }
}, { passive: true });

/* Cursor: ring lags behind, dot is instant — classic depth trick */
const ring = document.getElementById('cursor-ring');
const dot  = document.getElementById('cursor-dot');
const ringX = gsap.quickTo(ring, 'x', { duration: 0.62, ease: 'power3.out' });
const ringY = gsap.quickTo(ring, 'y', { duration: 0.62, ease: 'power3.out' });
const dotX  = gsap.quickTo(dot,  'x', { duration: 0.12, ease: 'power2.out' });
const dotY  = gsap.quickTo(dot,  'y', { duration: 0.12, ease: 'power2.out' });

document.querySelectorAll('.cta-button, .top-right').forEach(el => {
  el.addEventListener('pointerenter', () => document.body.classList.add('cursor-hover'));
  el.addEventListener('pointerleave', () => document.body.classList.remove('cursor-hover'));
});

/* Magnetic CTA */
const btn  = document.getElementById('enter-button');
const btnX = gsap.quickTo(btn, 'x', { duration: 0.85, ease: 'expo.out' });
const btnY = gsap.quickTo(btn, 'y', { duration: 0.85, ease: 'expo.out' });
let btnRect = null, rectStale = true;
const staleRect = () => { rectStale = true; };
addEventListener('resize', staleRect);

if (!coarse) {
  addEventListener('pointermove', e => {
    if (progress < 0.94) { btnX(0); btnY(0); return; }
    if (rectStale || !btnRect) { btnRect = btn.getBoundingClientRect(); rectStale = false; }
    const cx = btnRect.left + btnRect.width / 2;
    const cy = btnRect.top + btnRect.height / 2;
    const dx = e.clientX - cx, dy = e.clientY - cy;
    const pull = Math.hypot(dx, dy) < 170 ? 0.34 : 0;
    btnX(dx * pull); btnY(dy * pull);
  }, { passive: true });
}

/* ── 11 · SINGLE TICKER ────────────────────────────────────────────── */
let velSmooth = 0, spinIdle = 0;
let fpsAcc = 0, fpsFrames = 0, watchdog = true;

gsap.ticker.lagSmoothing(0);
gsap.ticker.add((time, deltaMS) => {
  const dt = Math.min(deltaMS / 1000, 1 / 30);   // clamp after tab switches

  lenis?.raf(time * 1000);

  /* — simulation — */
  U.uTime.value += dt;
  U.uScroll.value = damp(U.uScroll.value, progress, 6, dt);

  /* Integrated flow: continuous even while the speed changes */
  U.uFlow.value += dt * (3.0 + U.uScroll.value * 8.0);

  const vNorm = clamp(Math.abs(rawVelocity) / 2600, 0, 1);
  velSmooth = damp(velSmooth, vNorm, 5.5, dt);
  U.uVelocity.value = velSmooth;
  rawVelocity *= 0.9;

  /* Pointer energy decays when the cursor rests */
  pointerEnergy = damp(pointerEnergy, moving, moving ? 9 : 1.6, dt);
  U.uMouseStrength.value = pointerEnergy;
  moving = 0;

  if (coarse) {                                   /* touch: gentle auto-drift */
    const t = U.uTime.value;
    msx = 0.5 + Math.sin(t * 0.21) * 0.26;
    msy = 0.5 + Math.cos(t * 0.17) * 0.18;
    pointerEnergy = U.uMouseStrength.value = 0.55;
  }
  U.uMouseSmooth.value.x = damp(U.uMouseSmooth.value.x, msx, 3.4, dt);
  U.uMouseSmooth.value.y = damp(U.uMouseSmooth.value.y, msy, 3.4, dt);

  /* — camera: chases a scrubbed target, so it always trails with weight — */
  spinIdle += dt;
  const px = mx * 3.2, py = my * 1.1;
  camera.position.x = damp(camera.position.x, camTarget.x + px + Math.sin(spinIdle * 0.23) * 0.9, 2.2, dt);
  camera.position.y = damp(camera.position.y, camTarget.y + py + Math.cos(spinIdle * 0.19) * 0.5, 2.6, dt);
  camera.position.z = damp(camera.position.z, camTarget.z, 3.4, dt);
  lookAt.set(
    damp(lookAt.x, camera.position.x * 0.3 + px * 0.4, 2.4, dt),
    damp(lookAt.y, lookTarget.y, 2.4, dt),
    camera.position.z - 25);
  camera.lookAt(lookAt);

  if (dust) {
    dust.rotation.y += dt * 0.055;
    dust.position.y = Math.sin(U.uTime.value * 0.15) * 1.5;
    dust.position.z = (dust.position.z - dt * (2 + velSmooth * 14)) % 60;
  }

  /* — HUD (also damped, so numbers ease instead of snapping) — */
  hudP = damp(hudP, progress, 7, dt);
  setFill(hudP);
  $pct.textContent = String(Math.round(hudP * 100)).padStart(2, '0');

  for (let i = CHAPTERS.length - 1; i >= 0; i--) {
    if (progress >= CHAPTERS[i][0]) { setChapter(i); break; }
  }
  setStatus(progress < 0.14 ? 'SCROLL TO DIVE IN'
          : progress < 0.65 ? 'KEEP GOING'
          : progress < 0.94 ? 'ALMOST THERE' : '');

  /* — render — */
  if (!renderer) return;
  if (composer) {
    if (finalPass) {
      finalPass.uniforms.uTime.value = U.uTime.value;
      finalPass.uniforms.uAberration.value = damp(
        finalPass.uniforms.uAberration.value, velSmooth * 1.35, 6, dt);
    }
    composer.render();
  } else {
    renderer.render(scene, camera);
  }

  /* — adaptive watchdog — */
  fpsAcc += dt; fpsFrames++;
  if (fpsAcc >= 2) {
    const fps = fpsFrames / fpsAcc;
    if (watchdog && fps < 42 && composer) { composer = null; finalPass = null; }
    else if (watchdog && fps < 32) {
      renderer.setPixelRatio(1);
      U.uPixelRatio.value = 1;
      watchdog = false;
    }
    fpsAcc = 0; fpsFrames = 0;
  }
});

const lookAt = new THREE.Vector3(0, 0, -25);
let hudP = 0;

/* ── 12 · BOOT SEQUENCE ────────────────────────────────────────────── */
const setPre = gsap.quickSetter('#pre-fill', 'scaleX');
const $prePct = document.getElementById('pre-pct');
const loadState = { v: 0 };

const bootTl = gsap.timeline();
bootTl.to(loadState, {
  v: 1, duration: 1.7, ease: 'power2.inOut',
  onUpdate: () => {
    setPre(loadState.v);
    $prePct.textContent = String(Math.round(loadState.v * 100)).padStart(3, '0');
  },
});

/* Hold at 100% for a beat so the user registers it, then reveal */
bootTl.to({}, { duration: 0.9 });

function reveal() {
  document.body.classList.remove('is-loading');

  const tlIn = gsap.timeline({ defaults: { ease: 'expo.out' } });

  tlIn
    .to('#preloader', { opacity: 0, duration: 0.9, ease: 'power2.inOut',
                        onComplete: () => document.getElementById('preloader').remove() })
    .to('#webgl-canvas', { opacity: 1, duration: 2.2, ease: 'power2.out' }, 0.1)
    .fromTo(camera.position, { y: 34, z: 118 },
            { y: 12, z: 80, duration: 5.2, ease: 'power3.out' }, 0.15)
    .to('.intro-section', { opacity: 1, scale: 1, duration: 1.6 }, 0.4)
    .from(splitAll('.title-top-left'),
          { yPercent: 118, opacity: 0, duration: 1.5, stagger: 0.045 }, 0.55)
    .from(splitAll('.title-bottom-right'),
          { yPercent: 118, opacity: 0, duration: 1.5, stagger: 0.045 }, 0.72)
    .from(splitAll('.subtitle-center'),
          { yPercent: 105, opacity: 0, duration: 1.1, stagger: 0.018 }, 0.95)
    .from('.scroll-cue', { opacity: 0, scaleY: 0, transformOrigin: 'top center',
                           duration: 1.2 }, 1.35)
    .from('#hud .hud-corner', { opacity: 0, y: 12, duration: 1.2, stagger: 0.09 }, 1.0)
    .add(() => { lenis?.start(); ScrollTrigger.refresh(); }, 1.5);
}

Promise.all([
  bootTl.then(),
  document.fonts ? document.fonts.ready : Promise.resolve(),
  postPromise
]).then(reveal);

/* ── 13 · LIFECYCLE ────────────────────────────────────────────────── */
let resizeId;
addEventListener('resize', () => {
  clearTimeout(resizeId);
  resizeId = setTimeout(() => {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    U.uResolution.value.set(innerWidth, innerHeight);
    if (renderer) {
      renderer.setSize(innerWidth, innerHeight);
      renderer.setPixelRatio(Math.min(devicePixelRatio, Q.dpr));
      U.uPixelRatio.value = renderer.getPixelRatio();
      composer?.setSize(innerWidth, innerHeight);
    }
    ScrollTrigger.refresh();
  }, 160);
});

document.addEventListener('visibilitychange', () => {
  document.hidden ? gsap.ticker.sleep() : gsap.ticker.wake();
});

/* ── 14 · EXIT ─────────────────────────────────────────────────────── */
let leaving = false;
btn.addEventListener('click', () => {
  if (leaving) return;
  leaving = true;
  lenis?.stop();

  gsap.timeline({ defaults: { ease: 'power2.inOut' } })
    .to('.content-overlay', { opacity: 0, duration: 1.1 }, 0)
    .to('#hud',      { opacity: 0, duration: 0.9 }, 0)
    .to('.vignette', { opacity: 0, duration: 0.9 }, 0)
    .to(camTarget,   { z: -132, duration: 2.4, ease: 'power2.in' }, 0)
    .to(U.uMorph,    { value: 0, duration: 2.0, ease: 'power2.in' }, 0)
    .to(U.uSpotBase, { value: 2.2, duration: 2.0 }, 0)
    .add(() => { location.href = '/setup'; }, 2.5);
});
// WORKAROUND FOR WEBKITGTK POINTER EVENTS BUG
document.addEventListener('click', (e) => {
  const btn = document.getElementById('enter-button');
  if (btn) {
    const rect = btn.getBoundingClientRect();
    if (
      e.clientX >= rect.left &&
      e.clientX <= rect.right &&
      e.clientY >= rect.top &&
      e.clientY <= rect.bottom
    ) {
      if (!btn.disabled && typeof btn.click === 'function') {
         btn.click();
      }
    }
  }
});

document.addEventListener('click', (e) => {
  document.querySelectorAll('.info-btn').forEach(btn => {
    const rect = btn.getBoundingClientRect();
    if (
      e.clientX >= rect.left &&
      e.clientX <= rect.right &&
      e.clientY >= rect.top &&
      e.clientY <= rect.bottom
    ) {
      if (typeof btn.click === 'function') {
         // Some spans don't have click() by default but dispatchEvent works
         btn.dispatchEvent(new MouseEvent('click', {
            bubbles: true,
            cancelable: true,
            view: window
          }));
      }
    }
  });
});
