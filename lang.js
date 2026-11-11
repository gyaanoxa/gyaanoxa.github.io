// Language switcher (Google Translate, loaded only after a visitor picks a language) + local release times.
(function () {
  var LANGS = [
    ["", "Original", "हिन्दी + English"],
    ["en", "English", "English"],
    ["hi", "हिन्दी", "Hindi"],
    ["bn", "বাংলা", "Bengali"],
    ["mr", "मराठी", "Marathi"],
    ["te", "తెలుగు", "Telugu"],
    ["ta", "தமிழ்", "Tamil"],
    ["gu", "ગુજરાતી", "Gujarati"],
    ["kn", "ಕನ್ನಡ", "Kannada"],
    ["ml", "മലയാളം", "Malayalam"],
    ["pa", "ਪੰਜਾਬੀ", "Punjabi"],
    ["or", "ଓଡ଼ିଆ", "Odia"],
    ["ur", "اردو", "Urdu"],
    ["ne", "नेपाली", "Nepali"],
    ["es", "Español", "Spanish"],
    ["fr", "Français", "French"],
    ["de", "Deutsch", "German"],
    ["pt", "Português", "Portuguese"],
    ["ru", "Русский", "Russian"],
    ["ar", "العربية", "Arabic"],
    ["id", "Bahasa Indonesia", "Indonesian"],
    ["ja", "日本語", "Japanese"],
    ["zh-CN", "中文", "Chinese"]
  ];

  function current() {
    var m = document.cookie.match(/(?:^|;\s*)googtrans=\/[^/]*\/([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  function setCookie(val) {
    var host = location.hostname, exp = val ? "" : "; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    var v = val ? "/auto/" + val : "";
    document.cookie = "googtrans=" + v + "; path=/" + exp;
    if (host.indexOf(".") > 0) {
      document.cookie = "googtrans=" + v + "; path=/; domain=." + host.replace(/^www\./, "") + exp;
    }
  }

  function loadGoogle() {
    if (window.__gtLoaded) return;
    window.__gtLoaded = true;
    var holder = document.createElement("div");
    holder.id = "gt-holder";
    holder.style.display = "none";
    document.body.appendChild(holder);
    window.gtInit = function () {
      new google.translate.TranslateElement({ autoDisplay: false }, "gt-holder");
    };
    var s = document.createElement("script");
    s.src = "https://translate.google.com/translate_a/element.js?cb=gtInit";
    s.async = true;
    document.body.appendChild(s);
  }

  function build() {
    var slot = document.querySelector(".socials");
    if (!slot) return;
    var cur = current();
    var label = (LANGS.filter(function (l) { return l[0] === cur; })[0] || LANGS[0]);
    var wrap = document.createElement("div");
    wrap.className = "lang notranslate";
    wrap.setAttribute("translate", "no");
    wrap.innerHTML =
      '<button class="lang-btn" type="button" aria-haspopup="true" aria-expanded="false" aria-label="Change language">' +
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM3.6 9h16.8M3.6 15h16.8M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>' +
      '<span class="lang-cur">' + (cur ? label[1] : "Language") + "</span></button>" +
      '<div class="lang-menu" role="menu"><p class="lang-head">Read this site in</p></div>';
    var menu = wrap.querySelector(".lang-menu");
    LANGS.forEach(function (l) {
      var b = document.createElement("button");
      b.type = "button";
      b.setAttribute("role", "menuitem");
      b.className = "lang-item" + (l[0] === cur ? " on" : "");
      b.innerHTML = "<b>" + l[1] + "</b><small>" + l[2] + "</small>";
      b.onclick = function () {
        setCookie(l[0]);
        location.reload();
      };
      menu.appendChild(b);
    });
    var note = document.createElement("p");
    note.className = "lang-note";
    note.textContent = "Translated by Google. Video titles stay as on YouTube.";
    menu.appendChild(note);
    var btn = wrap.querySelector(".lang-btn");
    btn.onclick = function (e) {
      e.stopPropagation();
      var open = wrap.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    };
    document.addEventListener("click", function () { wrap.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") wrap.classList.remove("open"); });
    slot.insertBefore(wrap, slot.firstChild);
    if (cur) loadGoogle();
  }

  // Release times in the visitor's own time zone (shown only outside India)
  function localTimes() {
    var tz;
    try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (e) { return; }
    if (!tz || tz === "Asia/Kolkata" || tz === "Asia/Calcutta") return;
    document.querySelectorAll(".up[data-at]").forEach(function (el) {
      var t = new Date(el.getAttribute("data-at"));
      if (isNaN(t)) return;
      var s = t.toLocaleString(undefined, { weekday: "short", hour: "numeric", minute: "2-digit" });
      var d = document.createElement("div");
      d.className = "local notranslate";
      d.textContent = "Your time: " + s;
      var w = el.querySelector(".what");
      if (w) w.appendChild(d);
    });
  }

  // Total site visits from GoatCounter (shown only when the count loads)
  function visits() {
    var el = document.querySelector(".visits[data-on]");   // switched on by "show_views" in data/site.json
    if (!el || !window.fetch) return;
    fetch("https://gyaanoxa.goatcounter.com/counter/TOTAL.json").then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || !d.count) return;
        el.querySelector(".gc-total").textContent = d.count;
        el.hidden = false;
      }).catch(function () {});
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { build(); localTimes(); visits(); });
  } else { build(); localTimes(); visits(); }
})();
