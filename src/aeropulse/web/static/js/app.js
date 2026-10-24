// Progressive enhancement only. Every page works without this file.

const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
const day = new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", year: "numeric" });

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
    root.dataset.theme = next;
    try { localStorage.setItem("aeropulse-theme", next); } catch (e) { /* ignore */ }
    label();
  });
}

// ---------------------------------------------------------------- hero picker
function initHero(scope = document) {
  const hero = scope.querySelector("[data-hero]");
  if (!hero) return;
  const form = hero.querySelector("[data-hero-form]");
  if (!form) return;
  let inflight;

  // Remember the last route this browser asked about. Nothing leaves the browser.
  if (!location.search) {
    try {
      const saved = JSON.parse(localStorage.getItem("aeropulse-route") || "null");
      if (saved && saved.origin && (saved.origin !== form.origin.value || saved.dest !== form.dest.value
          || saved.w !== form.w.value)) {
        load(new URLSearchParams(saved), null, false);
      }
    } catch (e) { /* ignore */ }
  }

  form.addEventListener("change", (event) => {
    const params = new URLSearchParams(new FormData(form));
    if (event.target.name === "origin") params.delete("dest");
    load(params, event.target.id, true);
  });

  async function load(params, focusId, push) {
    inflight?.abort();
    inflight = new AbortController();
    hero.setAttribute("aria-busy", "true");
    try {
      const res = await fetch(`/fragments/hero?${params}`, { signal: inflight.signal });
      if (!res.ok) throw new Error(res.status);
      hero.innerHTML = await res.text();
      hero.querySelectorAll(".plot > svg, .today, .verdict").forEach((el) => {
        el.style.animation = "none";
      });
      initHero(hero.parentElement);
      initScrub(hero);
      const f = hero.querySelector("[data-hero-form]");
      const state = { origin: f.origin.value, dest: f.dest.value, w: f.w.value };
      try { localStorage.setItem("aeropulse-route", JSON.stringify(state)); } catch (e) { /* ignore */ }
      if (push) history.replaceState(null, "", `/?${new URLSearchParams(state)}`);
      if (focusId) document.getElementById(focusId)?.focus();
    } catch (e) {
      if (e.name !== "AbortError") form.submit();
    } finally {
      hero.removeAttribute("aria-busy");
    }
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
      tip.style.left = `${Math.min(Math.max(x, 12), 88)}%`;
      tip.style.top = `${Math.max(y - 6, 0)}%`;
      const fmt = (v) => (isRupees ? `₹${inr.format(v)}` : v.toFixed(1));
      const range = low != null ? `<br>95% range ${fmt(low)}–${fmt(high)}` : "";
      const count = n ? ` · ${n} prices` : "";
      tip.innerHTML = `<b>${fmt(value)}</b> on ${day.format(new Date(date))}${range}${count}`;
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
