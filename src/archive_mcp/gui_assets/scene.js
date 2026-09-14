"use strict";
// All scenery and provider marks are bundled; the room never fetches an asset.
const logoNames = {
  chatgpt: "openai",
  codex: "codex",
  claude: "claude",
  "claude-code": "claude",
  "claude-context": "claude",
  gemini: "gemini",
  deepseek: "deepseek",
  grok: "grok",
  "qwen-code": "qwen",
  opencode: "opencode",
  antigravity: "antigravity",
  notebooklm: "notebooklm",
};
function providerMark(provider) {
  const source = providerLogos[logoNames[provider]];
  if (source) {
    const mark = el("img", undefined, "provider-logo");
    mark.src = source;
    mark.alt = "";
    return mark;
  }
  return el("span", provider === "zcode" ? "ZC" : "✧", "provider-monogram");
}
function providerBadge(provider) {
  const badge = el("span", undefined, "badge");
  badge.append(providerMark(provider), el("span", provider));
  return badge;
}
function buildBottles(formats) {
  // Preserve the controls while a status refresh follows an import.
  if ($("bottle-rack").children.length) return;
  for (const [key, description] of Object.entries(formats)) {
    const [name, kind] = description.split(" · ");
    const bottle = el("button", undefined, "provider-bottle");
    bottle.type = "button";
    bottle.dataset.provider = key;
    bindAttribute(
      bottle,
      "aria-label",
      key === "auto"
        ? "Unmarked bottle: auto-detect all supported formats"
        : description,
    );
    bottle.setAttribute(
      "aria-pressed",
      String(key === $("source-format").value),
    );
    const vial = el("span", undefined, "vial"),
      body = el("span", undefined, "vial-body");
    const mark = el("span", undefined, "vial-mark");
    if (key !== "auto") mark.append(providerMark(key));
    body.append(mark);
    vial.append(
      el("span", undefined, "vial-cork"),
      el("span", undefined, "vial-art"),
      body,
    );
    bottle.append(
      vial,
      ui("span", key === "auto" ? "Unmarked" : name, "bottle-name"),
      ui(
        "span",
        key === "auto" ? "Auto-detect all" : kind || "Saved context",
        "bottle-kind",
      ),
    );
    bottle.onclick = () => {
      $("source-format").value = key;
      $("source-format").onchange();
      bindUI($("selected-format"), description);
      for (const item of $("bottle-rack").children)
        item.setAttribute("aria-pressed", String(item === bottle));
    };
    $("bottle-rack").append(bottle);
  }
}
const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
let still = motionPreference.matches,
  entering = false,
  pouring = false;
function applyMotion() {
  document.body.classList.toggle("still", still);
  $("motion-toggle").setAttribute("aria-pressed", String(still));
  bindUI($("motion-toggle"), still ? "Wake the magic" : "Still the magic");
  restartSmoke();
}
$("motion-toggle").onclick = () => {
  still = !still;
  applyMotion();
};
motionPreference.addEventListener("change", (event) => {
  still = event.matches;
  applyMotion();
});
function closeWorkbench() {
  if (pouring || state.importing) return;
  if ($("reader-dialog").open) $("reader-dialog").close();
  $("workbench").close();
}
$("close-workbench").onclick = closeWorkbench;
$("workbench").addEventListener("cancel", (event) => {
  if (pouring || state.importing) event.preventDefault();
});
$("workbench").addEventListener("close", () => {
  if (pouring) return;
  state.page = "room";
  state.searchGeneration++;
  document.body.dataset.scene = "room";
  $("pensieve").focus({ preventScroll: true });
});
function openDoor(skip = false) {
  if (entering) return;
  entering = true;
  document.body.dataset.scene = "room";
  $("entry").classList.add("opening");
  const complete = () => {
    $("entry").hidden = true;
    $("chamber").inert = false;
    state.page = "room";
    entering = false;
    $("pensieve").focus({ preventScroll: true });
    smokeBurst(24);
    if (still) restartSmoke();
  };
  if (skip || still) complete();
  else setTimeout(complete, 1900);
}
$("open-door").onclick = () => openDoor();
$("skip-door").onclick = () => openDoor(true);
$("return-door").onclick = () => {
  $("basin-menu").hidden = true;
  $("pensieve").setAttribute("aria-expanded", "false");
  $("chamber").inert = true;
  $("entry").hidden = false;
  $("entry").classList.remove("opening");
  document.body.dataset.scene = state.page = "door";
  $("open-door").focus({ preventScroll: true });
};
$("pensieve").onclick = () => {
  const visible = $("basin-menu").hidden;
  $("basin-menu").hidden = !visible;
  $("pensieve").setAttribute("aria-expanded", String(visible));
  if (visible) {
    smokeBurst(45);
    $("scene-import").focus({ preventScroll: true });
  }
};
$("scene-import").onclick = () => show("import");
$("scene-search").onclick = () => show("search");
$("bottle-shelf").onclick = () => show("library");
$("orb-shelf").onclick = () => show("library");
async function pourMemory() {
  bindUI($("scene-status"), "Your memory has reached the Pensieve.");
  if (!still) {
    pouring = true;
    $("pour-vial").replaceChildren(
      $("bottle-rack")
        .querySelector('[aria-pressed="true"] .vial')
        .cloneNode(true),
    );
    $("workbench").close();
    $("chamber").inert = true;
    $("pour-ritual").hidden = false;
    smokeBurst(60);
    await new Promise((resolve) => setTimeout(resolve, 3400));
    $("pour-ritual").hidden = true;
    $("chamber").inert = false;
    $("workbench").showModal();
    pouring = false;
  }
  setTimeout(() => {
    bindUI($("scene-status"), "");
  }, 3500);
}
// Low-resolution, capped smoke particles drift from the water and react to the pointer.
// No continuous animation runs while the window is hidden or motion is disabled.
const canvas = $("smoke"),
  ctx = canvas.getContext("2d");
const puff = document.createElement("canvas");
puff.width = puff.height = 96;
const puffContext = puff.getContext("2d"),
  gradient = puffContext.createRadialGradient(48, 48, 0, 48, 48, 48);
gradient.addColorStop(0, "rgba(225,239,245,.24)");
gradient.addColorStop(0.35, "rgba(192,216,233,.13)");
gradient.addColorStop(1, "rgba(172,200,224,0)");
puffContext.fillStyle = gradient;
puffContext.fillRect(0, 0, 96, 96);
let particles = [],
  frame = 0,
  previous = 0,
  spawnTime = 0;
const pointer = { x: -1000, y: -1000 };
function emitter() {
  const rect = $("room-stage").getBoundingClientRect();
  return document.body.dataset.scene === "search"
    ? { x: innerWidth * 0.5, y: innerHeight * 0.66, spread: innerWidth * 0.31 }
    : {
        x: rect.left + rect.width * 0.5,
        y: rect.top + rect.height * 0.42,
        spread: rect.width * 0.24,
      };
}
function addPuff(age = 0) {
  if (particles.length >= 150) return;
  const source = emitter();
  particles.push({
    x: source.x + (Math.random() - 0.5) * source.spread,
    y: source.y,
    age,
    life: 4 + Math.random() * 4,
    phase: Math.random() * 6.28,
    size: 45 + Math.random() * 70,
    vx: (Math.random() - 0.5) * 12,
  });
}
function smokeBurst(count) {
  if (still) return;
  for (let i = 0; i < count; i++) addPuff(Math.random() * 1.5);
}
function drawSmoke(dt) {
  ctx.clearRect(0, 0, innerWidth, innerHeight);
  if (document.body.dataset.scene === "door") return;
  for (const p of particles) {
    p.age += dt;
    p.x += (p.vx + Math.sin(p.age * 1.7 + p.phase) * 12) * dt;
    p.y -= (12 + Math.sin(p.phase) * 4) * dt;
    const dx = p.x - pointer.x,
      dy = p.y - pointer.y,
      distance = Math.hypot(dx, dy);
    if (distance > 1 && distance < 160) {
      p.x += (dx / distance) * 35 * dt;
      p.y += (dy / distance) * 25 * dt;
    }
    const size = p.size * (1 + p.age * 0.19);
    ctx.globalAlpha = Math.max(0, Math.sin((Math.PI * p.age) / p.life)) * 0.72;
    ctx.drawImage(puff, p.x - size / 2, p.y - size / 2, size, size);
  }
  particles = particles.filter((p) => p.age < p.life);
  ctx.globalAlpha = 1;
}
function animateSmoke(time) {
  frame = requestAnimationFrame(animateSmoke);
  if (time - previous < 33) return;
  const dt = Math.min((time - previous) / 1000, 0.07);
  previous = time;
  spawnTime += dt;
  if (spawnTime > 0.13) {
    addPuff();
    spawnTime = 0;
  }
  drawSmoke(dt);
}
function restartSmoke() {
  cancelAnimationFrame(frame);
  if (document.hidden) return;
  if (still) {
    particles = [];
    for (let i = 0; i < 25; i++) addPuff(1 + Math.random() * 3);
    drawSmoke(0);
  } else {
    previous = performance.now();
    frame = requestAnimationFrame(animateSmoke);
  }
}
function resizeSmoke() {
  const scale = Math.min(window.devicePixelRatio || 1, 1.5);
  canvas.width = Math.round(innerWidth * scale);
  canvas.height = Math.round(innerHeight * scale);
  ctx.setTransform(scale, 0, 0, scale, 0, 0);
  restartSmoke();
}
window.addEventListener("resize", resizeSmoke);
window.addEventListener(
  "pointermove",
  (event) => {
    pointer.x = event.clientX;
    pointer.y = event.clientY;
  },
  { passive: true },
);
document.addEventListener("pointerleave", () => {
  pointer.x = pointer.y = -1000;
});
document.addEventListener("visibilitychange", restartSmoke);
resizeSmoke();
applyMotion();

window.addEventListener("keydown", (event) => {
  if (event.key === "Tab") document.body.classList.add("keyboard");
});
window.addEventListener(
  "pointerdown",
  () => document.body.classList.remove("keyboard"),
  { passive: true },
);
new MutationObserver(() => {
  if (still) restartSmoke();
}).observe(document.body, {
  attributes: true,
  attributeFilter: ["data-scene"],
});
