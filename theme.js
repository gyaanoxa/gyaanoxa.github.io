/* Theme switcher: Dark / Light / System and three colour palettes. The choice is kept in this browser only. */
(function () {
  var root = document.documentElement, KM = "gx-mode", KP = "gx-palette", PALS = ["indigo", "saffron", "forest"];
  function get(k, d) { try { return localStorage.getItem(k) || d; } catch (e) { return d; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  var mq = window.matchMedia ? window.matchMedia("(prefers-color-scheme: light)") : null;
  function resolve(m) { return m === "system" ? (mq && mq.matches ? "light" : "dark") : (m === "light" ? "light" : "dark"); }
  function apply() {
    var m = get(KM, "system"), p = get(KP, "indigo");
    if (PALS.indexOf(p) < 0) p = "indigo";
    root.setAttribute("data-mode", m);
    root.setAttribute("data-theme", resolve(m));
    root.setAttribute("data-palette", p);
    var bg = getComputedStyle(root).getPropertyValue("--bg-2").trim(), tag = document.querySelector('meta[name="theme-color"]');
    if (tag && bg) tag.setAttribute("content", bg);
    document.querySelectorAll(".theme [data-mode]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.mode === m)); });
    document.querySelectorAll(".theme [data-palette]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.palette === p)); });
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest(".theme button");
    if (b) {
      if (b.dataset.mode) set(KM, b.dataset.mode);
      if (b.dataset.palette) set(KP, b.dataset.palette);
      apply();
      return;
    }
    document.querySelectorAll("details.theme[open]").forEach(function (d) { if (!d.contains(e.target)) d.removeAttribute("open"); });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") document.querySelectorAll("details.theme[open]").forEach(function (d) { d.removeAttribute("open"); });
  });
  if (mq && mq.addEventListener) mq.addEventListener("change", function () { if (get(KM, "system") === "system") apply(); });
  apply();
})();
