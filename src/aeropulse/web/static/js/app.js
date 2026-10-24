// Progressive enhancement only. Every page works without this file.

const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
const day = new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", year: "numeric" });
const calm = matchMedia("(prefers-reduced-motion: reduce)");

// ---------------------------------------------------------------- theme toggle
function initTheme() {
  const btn = document.querySelector("[data-theme-toggle]");
  if (!btn) return;
  const root = document.documentElement;
  const current = () =>
    root.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const label = () => btn.setAttribute("aria-label",
    current() === "dark" ? "Switch to light theme" : "Switch to dark theme");
  label();
  btn.addEventListener("click", () => {
    root.dataset.theme = current() === "dark" ? "light" : "dark";
    label();
    try { localStorage.setItem("aeropulse-theme", root.dataset.theme); } catch (e) { /* ignore */ }
  });
}

// ---------------------------------------------------------------- planes
// The only continuous motion on the site. Paused for readers who prefer less motion.
function settleMotion(scope = document) {
  if (calm.matches) scope.querySelectorAll("svg").forEach((s) => s.pauseAnimations?.());
}

// ---------------------------------------------------------------- route chart
function initChart(scope, onPick) {
  const chart = scope.querySelector("[data-map]");
  if (!chart) return;
  const tip = chart.querySelector(".map-tip");
  if (chart.querySelector(".airway.is-selected")) chart.classList.add("has-selection");

  const show = (link, event) => {
    chart.classList.add("is-hovering");
    chart.querySelectorAll(`.airway[data-route="${link.dataset.route}"]`)
      .forEach((el) => el.classList.add("is-hot"));
    tip.innerHTML = `<b>${link.dataset.name}</b>${link.dataset.state}`;
    tip.hidden = false;
    const box = chart.getBoundingClientRect();
    let x, y;
    if (event && "clientX" in event) { x = event.clientX - box.left; y = event.clientY - box.top; }
    else {
      const r = link.getBoundingClientRect();
      x = r.left + r.width / 2 - box.left; y = r.top + r.height / 2 - box.top;
    }
    tip.style.left = `${Math.min(Math.max(x, 90), box.width - 90)}px`;
    tip.style.top = `${y}px`;
  };
  const hide = () => {
    chart.classList.remove("is-hovering");
    chart.querySelectorAll(".is-hot").forEach((el) => el.classList.remove("is-hot"));
    tip.hidden = true;
  };

  chart.querySelectorAll(".lane-hit").forEach((link) => {
    link.addEventListener("pointermove", (e) => show(link, e));
    link.addEventListener("pointerleave", hide);
    link.addEventListener("focus", () => show(link));
    link.addEventListener("blur", hide);
    link.addEventListener("click", (e) => {
      if (!onPick || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
      e.preventDefault();
      hide();
      onPick(link.dataset.route);
    });
  });
}

// ---------------------------------------------------------------- hero
function initHero() {
  const hero = document.querySelector("[data-hero]");
  if (!hero) return;
  let inflight;

  const bind = () => {
    const form = hero.querySelector("[data-hero-form]");
    initChart(hero, (route) => {
      const [origin, dest] = route.split("-");
      load(new URLSearchParams({ origin, dest, w: form?.w.value ?? "" }), null);
    });
    initScrub(hero);
    settleMotion(hero);
    if (!form) return;
    form.addEventListener("change", (event) => {
      const params = new URLSearchParams(new FormData(form));
      if (event.target.name === "origin") params.delete("dest");
      load(params, event.target.id);
    });
    form.querySelector("[data-swap]")?.addEventListener("click", () => {
      load(new URLSearchParams({ origin: form.dest.value, dest: form.origin.value, w: form.w.value }), "f-origin");
    });
  };

  async function load(params, focusId, remember = true) {
    inflight?.abort();
    inflight = new AbortController();
    hero.querySelector("[data-hero-copy]")?.setAttribute("aria-busy", "true");
    try {
      const res = await fetch(`/fragments/hero?${params}`, { signal: inflight.signal });
      if (!res.ok) throw new Error(String(res.status));
      const html = await res.text();
      const swap = () => {
        hero.innerHTML = html;
        hero.querySelector("[data-hero-copy]")?.classList.add("is-swapping");
        bind();
      };
      if (document.startViewTransition && !calm.matches) await document.startViewTransition(swap).updateCallbackDone;
      else swap();
      const form = hero.querySelector("[data-hero-form]");
      if (form && remember) {
        const state = { origin: form.origin.value, dest: form.dest.value, w: form.w.value };
        try { localStorage.setItem("aeropulse-route", JSON.stringify(state)); } catch (e) { /* ignore */ }
        history.replaceState(null, "", `/?${new URLSearchParams(state)}`);
      }
      if (focusId) document.getElementById(focusId)?.focus();
    } catch (e) {
      if (e.name !== "AbortError") location.href = `/?${params}`;
    }
  }

  bind();

  // Show the last route this browser asked about. Nothing leaves the browser.
  if (!location.search) {
    try {
      const saved = JSON.parse(localStorage.getItem("aeropulse-route") || "null");
      const form = hero.querySelector("[data-hero-form]");
      if (saved?.origin && form && (saved.origin !== form.origin.value || saved.dest !== form.dest.value
          || saved.w !== form.w.value)) load(new URLSearchParams(saved), null, false);
    } catch (e) { /* ignore */ }
  }
}

// ---------------------------------------------------------------- chart scrubbing
function initScrub(scope = document) {
  scope.querySelectorAll(".plot[data-points]").forEach((plot) => {
    if (plot.dataset.scrub) return;
    plot.dataset.scrub = "1";
    const pts = JSON.parse(plot.dataset.points);
    if (pts.length < 2) return;
    const lo = parseFloat(plot.dataset.lo), hi = parseFloat(plot.dataset.hi);
    const isRupees = pts[0][1] > 500;
    const overlay = plot.querySelector(".overlay");
    const line = document.createElement("span");
    line.className = "crosshair";
    const tip = document.createElement("span");
    tip.className = "readout";
    tip.setAttribute("role", "status");
    let index = pts.length - 1;

    plot.tabIndex = 0;
    plot.setAttribute("aria-roledescription", "chart. Use left and right arrow keys to read values");

    const show = (i) => {
      index = Math.max(0, Math.min(pts.length - 1, i));
      const [date, value, low, high, n] = pts[index];
      const x = (index / (pts.length - 1)) * 100;
      const y = (1 - (value - lo) / (hi - lo)) * 100;
      line.style.left = `${x}%`;
      tip.style.left = `${Math.min(Math.max(x, 14), 86)}%`;
      tip.style.top = `${Math.max(y - 6, 0)}%`;
      const fmt = (v) => (isRupees ? `₹${inr.format(v)}` : v.toFixed(1));
      const range = low != null ? `<br>95% range ${fmt(low)}–${fmt(high)}` : "";
      const count = n ? `, ${n} prices` : "";
      tip.innerHTML = `<b>${fmt(value)}</b> on ${day.format(new Date(date))}${count}${range}`;
      if (!line.isConnected) overlay.append(line, tip);
    };
    const hide = () => { line.remove(); tip.remove(); };
    const fromEvent = (e) => {
      const r = overlay.getBoundingClientRect();
      return Math.round(((e.clientX - r.left) / r.width) * (pts.length - 1));
    };
    plot.addEventListener("pointermove", (e) => show(fromEvent(e)));
    plot.addEventListener("pointerdown", (e) => show(fromEvent(e)));
    plot.addEventListener("pointerleave", hide);
    plot.addEventListener("blur", hide);
    plot.addEventListener("focus", () => show(index));
    plot.addEventListener("keydown", (e) => {
      const step = e.shiftKey ? 7 : 1;
      if (e.key === "ArrowLeft") show(index - step);
      else if (e.key === "ArrowRight") show(index + step);
      else if (e.key === "Home") show(0);
      else if (e.key === "End") show(pts.length - 1);
      else if (e.key === "Escape") hide();
      else return;
      e.preventDefault();
    });
  });
}

// ---------------------------------------------------------------- copy buttons
function initCopy() {
  document.querySelectorAll("[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const source = document.querySelector(btn.dataset.copy);
      if (!source) return;
      try {
        await navigator.clipboard.writeText(source.textContent.trim());
        const original = btn.textContent;
        btn.textContent = "Copied";
        setTimeout(() => { btn.textContent = original; }, 1600);
      } catch (e) {
        const range = document.createRange();
        range.selectNodeContents(source);
        getSelection().removeAllRanges();
        getSelection().addRange(range);
      }
    });
  });
}

initTheme();
initHero();
initScrub();
initCopy();
settleMotion();
calm.addEventListener?.("change", () => document.querySelectorAll("svg").forEach((s) =>
  (calm.matches ? s.pauseAnimations?.() : s.unpauseAnimations?.())));
