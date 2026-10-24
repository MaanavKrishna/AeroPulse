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
    const next = current() === "dark" ? "light" : "dark";
    const apply = () => { root.dataset.theme = next; label(); };
    if (document.startViewTransition && !calm.matches) document.startViewTransition(apply);
    else apply();
    try { localStorage.setItem("aeropulse-theme", next); } catch (e) { /* ignore */ }
  });
}

// ---------------------------------------------------------------- fare count-up
// Counts from the route's usual fare to today's, so the number itself shows the move.
function countUp(scope = document, from = null) {
  scope.querySelectorAll(".fare[data-count-to]").forEach((el) => {
    const to = Number(el.dataset.countTo);
    const start = from ?? Number(el.dataset.countFrom ?? to);
    if (calm.matches || !Number.isFinite(start) || start === to) return;
    const t0 = performance.now();
    const dur = 900;
    const step = (now) => {
      const t = Math.min(1, (now - t0) / dur);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = `₹${inr.format(start + (to - start) * eased)}`;
      if (t < 1) requestAnimationFrame(step);
    };
    el.textContent = `₹${inr.format(start)}`;
    requestAnimationFrame(step);
  });
}

// ---------------------------------------------------------------- route map
function initMap(onPick) {
  const map = document.querySelector("[data-map]");
  if (!map) return null;
  const svg = map.querySelector("svg");
  const tip = map.querySelector(".map-tip");
  if (calm.matches) svg.pauseAnimations?.();
  calm.addEventListener?.("change", () => (calm.matches ? svg.pauseAnimations?.() : svg.unpauseAnimations?.()));

  const parts = (route) => map.querySelectorAll(`.arc[data-route="${route}"], .plane[data-route="${route}"]`);
  const ends = (route) => route.split("-").map((c) => map.querySelector(`.airport[data-code="${c}"]`));

  const select = (route) => {
    map.querySelectorAll(".is-selected").forEach((el) => el.classList.remove("is-selected"));
    map.querySelectorAll(".airport.is-end").forEach((el) => el.classList.remove("is-end"));
    if (!route) { map.classList.remove("has-selection"); return; }
    parts(route).forEach((el) => el.classList.add("is-selected"));
    ends(route).forEach((el) => el?.classList.add("is-end"));
    // keep the selected arc on top of the others
    const arc = map.querySelector(`.arc[data-route="${route}"]`);
    arc?.parentNode.append(arc);
    map.classList.add("has-selection");
  };

  const hot = (link, event) => {
    const route = link.dataset.route;
    map.classList.add("is-hovering");
    parts(route).forEach((el) => el.classList.add("is-hot"));
    tip.innerHTML = `<b>${link.dataset.name}</b>${link.dataset.state}`;
    tip.hidden = false;
    const box = map.getBoundingClientRect();
    let x, y;
    if (event && "clientX" in event) { x = event.clientX - box.left; y = event.clientY - box.top; }
    else {
      const r = link.getBoundingClientRect();
      x = r.left + r.width / 2 - box.left; y = r.top + r.height / 2 - box.top;
    }
    tip.style.left = `${Math.min(Math.max(x, 90), box.width - 90)}px`;
    tip.style.top = `${y}px`;
  };
  const cold = () => {
    map.classList.remove("is-hovering");
    map.querySelectorAll(".is-hot").forEach((el) => el.classList.remove("is-hot"));
    tip.hidden = true;
  };

  map.querySelectorAll(".arc-hit").forEach((link) => {
    link.addEventListener("pointermove", (e) => hot(link, e));
    link.addEventListener("pointerleave", cold);
    link.addEventListener("focus", () => hot(link));
    link.addEventListener("blur", cold);
    link.addEventListener("click", (e) => {
      if (!onPick || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
      e.preventDefault();
      cold();
      onPick(link.dataset.route);
    });
  });

  const initial = map.closest("[data-hero]")?.querySelector(".answer")?.dataset.route;
  if (initial) select(initial);
  return { select };
}

// ---------------------------------------------------------------- hero picker
function initHero() {
  const hero = document.querySelector("[data-hero]");
  if (!hero) return;
  const copy = hero.querySelector("[data-hero-copy]");
  let inflight;
  const map = initMap((route) => {
    const [origin, dest] = route.split("-");
    const w = copy.querySelector("[name=w]")?.value;
    load(new URLSearchParams({ origin, dest, w }), null);
    copy.scrollIntoView({ behavior: calm.matches ? "auto" : "smooth", block: "start" });
  });

  const bind = () => {
    const form = copy.querySelector("[data-hero-form]");
    if (!form) return;
    form.addEventListener("change", (event) => {
      const params = new URLSearchParams(new FormData(form));
      if (event.target.name === "origin") params.delete("dest");
      load(params, event.target.id);
    });
    form.querySelector("[data-swap]")?.addEventListener("click", () => {
      const params = new URLSearchParams({ origin: form.dest.value, dest: form.origin.value, w: form.w.value });
      load(params, "f-origin");
    });
    initScrub(copy);
  };

  // Remember the last route this browser asked about. Nothing leaves the browser.
  if (!location.search) {
    try {
      const saved = JSON.parse(localStorage.getItem("aeropulse-route") || "null");
      const form = copy.querySelector("[data-hero-form]");
      if (saved?.origin && form && (saved.origin !== form.origin.value || saved.dest !== form.dest.value
          || saved.w !== form.w.value)) load(new URLSearchParams(saved), null, false);
    } catch (e) { /* ignore */ }
  }

  async function load(params, focusId, remember = true) {
    inflight?.abort();
    inflight = new AbortController();
    copy.setAttribute("aria-busy", "true");
    const previous = Number(copy.querySelector(".fare[data-count-to]")?.dataset.countTo);
    try {
      const res = await fetch(`/fragments/hero?${params}`, { signal: inflight.signal });
      if (!res.ok) throw new Error(String(res.status));
      const html = await res.text();
      const swap = () => {
        copy.innerHTML = html;
        copy.classList.add("is-swapping");
        bind();
      };
      if (document.startViewTransition && !calm.matches) await document.startViewTransition(swap).updateCallbackDone;
      else swap();
      countUp(copy, Number.isFinite(previous) ? previous : null);
      const form = copy.querySelector("[data-hero-form]");
      const state = { origin: form.origin.value, dest: form.dest.value, w: form.w.value };
      map?.select(copy.querySelector(".answer")?.dataset.route);
      if (remember) {
        try { localStorage.setItem("aeropulse-route", JSON.stringify(state)); } catch (e) { /* ignore */ }
        history.replaceState(null, "", `/?${new URLSearchParams(state)}`);
      }
      if (focusId) document.getElementById(focusId)?.focus();
    } catch (e) {
      if (e.name !== "AbortError") location.href = `/?${params}`;
    } finally {
      copy.removeAttribute("aria-busy");
    }
  }

  bind();
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

// ---------------------------------------------------------------- page-level motion
function initFlight() {
  if (calm.matches) document.querySelectorAll(".flight svg").forEach((s) => s.pauseAnimations?.());
}

initTheme();
initHero();
initScrub();
initCopy();
initFlight();
countUp();
