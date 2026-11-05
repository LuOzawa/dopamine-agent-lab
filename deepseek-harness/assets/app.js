/* DeepSeek Harness 学习手册 — 进度、目录、搜索 */
(function () {
  "use strict";

  var KEY = "dsh-handbook:v1";
  var STAGE_TOTAL = { 1: 4, 2: 6, 3: 8, 4: 4, 5: 6, 6: 5 };
  var TOTAL = Object.keys(STAGE_TOTAL).reduce(function (n, k) { return n + STAGE_TOTAL[k]; }, 0);
  var state = load();

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      var obj = raw ? JSON.parse(raw) : {};
      return obj && typeof obj === "object" ? obj : {};
    } catch (e) { return {}; }
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  }
  function pct(a, b) { return b ? Math.round((a / b) * 100) : 0; }
  function validId(id) { return /^s[1-6]-\d+$/.test(id); }
  function stageDone(n) {
    var c = 0;
    Object.keys(state).forEach(function (k) {
      if (state[k] && k.indexOf("s" + n + "-") === 0) c++;
    });
    return Math.min(c, STAGE_TOTAL[n] || 0);
  }

  var toastEl = null, timer = null;
  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "toast";
      toastEl.setAttribute("role", "status");
      toastEl.setAttribute("aria-live", "polite");
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    clearTimeout(timer);
    timer = setTimeout(function () { toastEl.classList.remove("show"); }, 2200);
  }

  function render() {
    document.querySelectorAll("[data-done-id]").forEach(function (btn) {
      var id = btn.getAttribute("data-done-id");
      var done = !!state[id];
      btn.setAttribute("aria-pressed", done ? "true" : "false");
      var label = btn.querySelector(".label-text");
      if (label) label.textContent = done ? "已完成" : "标记完成";
      var card = btn.closest(".lesson");
      if (card) card.classList.toggle("is-done", done);
    });

    document.querySelectorAll("[data-stage-bar]").forEach(function (bar) {
      var n = Number(bar.getAttribute("data-stage-bar"));
      var c = stageDone(n);
      var fill = bar.querySelector("i");
      if (fill) fill.style.width = pct(c, STAGE_TOTAL[n]) + "%";
      var lab = document.querySelector('[data-stage-label="' + n + '"]');
      if (lab) lab.textContent = c + " / " + STAGE_TOTAL[n];
    });

    var all = Object.keys(state).filter(function (k) { return state[k] && validId(k); }).length;
    document.querySelectorAll("[data-mini-bar]").forEach(function (el) {
      el.style.width = pct(Math.min(all, TOTAL), TOTAL) + "%";
    });
    document.querySelectorAll("[data-mini-text]").forEach(function (el) {
      el.textContent = Math.min(all, TOTAL) + "/" + TOTAL;
    });
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-done-id]");
    if (btn) {
      var id = btn.getAttribute("data-done-id");
      state[id] = !state[id];
      if (!state[id]) delete state[id];
      save(); render();
      if (state[id]) {
        var n = Number((id.match(/^s(\d)-/) || [])[1]);
        var c = stageDone(n);
        toast(c === STAGE_TOTAL[n] ? "第 " + n + " 章全部完成" : "已标记完成 · 本章 " + c + "/" + STAGE_TOTAL[n]);
      }
      return;
    }
    var reset = e.target.closest("[data-reset]");
    if (reset && window.confirm("确定清空本机学习进度？")) {
      state = {}; save(); render(); toast("进度已清空");
    }
  });

  function initToc() {
    var links = Array.prototype.slice.call(document.querySelectorAll(".toc a[href^='#']"));
    if (!links.length || !("IntersectionObserver" in window)) return;
    var map = {};
    links.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
    var sections = links.map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); }).filter(Boolean);
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        links.forEach(function (a) { a.classList.remove("active"); });
        if (map[en.target.id]) map[en.target.id].classList.add("active");
      });
    }, { rootMargin: "-18% 0px -68% 0px", threshold: 0 });
    sections.forEach(function (s) { io.observe(s); });
  }

  function initReadBar() {
    var bar = document.querySelector(".read-progress");
    if (!bar) return;
    var update = function () {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
    };
    document.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  function initCatalog() {
    document.querySelectorAll("[data-lesson]").forEach(function (row) {
      row.classList.toggle("is-done", !!state[row.getAttribute("data-lesson")]);
    });
    var q = document.getElementById("catalog-q");
    if (!q) return;
    var rows = Array.prototype.slice.call(document.querySelectorAll(".chapter-row"));
    var count = document.getElementById("catalog-count");
    var empty = document.getElementById("catalog-empty");
    function apply() {
      var v = q.value.trim().toLowerCase(), n = 0;
      rows.forEach(function (r) {
        var hit = !v || r.textContent.toLowerCase().indexOf(v) !== -1;
        r.hidden = !hit;
        if (hit) n++;
      });
      if (count) count.textContent = n + " 项";
      if (empty) empty.hidden = n > 0;
    }
    q.addEventListener("input", apply);
  }

  function initSearch() {
    var input = document.getElementById("search-q");
    if (!input) return;
    var data = window.__DSH_INDEX__;
    var results = document.getElementById("search-results");
    var count = document.getElementById("search-count");
    var empty = document.getElementById("search-empty");
    var idle = document.getElementById("search-idle");
    var meta = document.getElementById("search-index-meta");
    if (!data || !data.lessons) { if (count) count.textContent = "索引未加载"; return; }
    if (meta) {
      var total = data.lessons.reduce(function (n, l) { return n + l.sentences.length; }, 0);
      meta.textContent = data.count + " 节 · " + total + " 句 · 索引 " + data.generated;
    }
    function escapeHtml(s) {
      return String(s).replace(/[&<>"']/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
      });
    }
    function escapeRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
    function highlight(text, terms) {
      var out = escapeHtml(text);
      terms.slice().sort(function (a, b) { return b.length - a.length; }).forEach(function (t) {
        out = out.replace(new RegExp("(" + escapeRe(escapeHtml(t)) + ")", "gi"), "<mark>$1</mark>");
      });
      return out;
    }
    function clip(text, terms) {
      if (text.length <= 150) return text;
      var low = text.toLowerCase(), idx = -1;
      terms.forEach(function (t) { var i = low.indexOf(t); if (i !== -1 && (idx === -1 || i < idx)) idx = i; });
      var start = Math.max(0, idx - 45), end = Math.min(text.length, start + 170);
      if (end - start < 140) start = Math.max(0, end - 170);
      return (start > 0 ? "…" : "") + text.slice(start, end) + (end < text.length ? "…" : "");
    }
    function render(raw) {
      var q = (raw || "").trim();
      var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
      if (!terms.length) {
        results.innerHTML = ""; count.textContent = "输入关键词开始";
        empty.hidden = true; if (idle) idle.hidden = false;
        return;
      }
      if (idle) idle.hidden = true;
      var hits = [];
      data.lessons.forEach(function (l) {
        var score = 0, snips = [];
        var title = l.title.toLowerCase();
        terms.forEach(function (t) { if (title.indexOf(t) !== -1) score += 6; });
        l.sentences.forEach(function (s) {
          var low = s.t.toLowerCase();
          var all = terms.every(function (t) { return low.indexOf(t) !== -1; });
          var some = terms.some(function (t) { return low.indexOf(t) !== -1; });
          if (all) { score += 3; snips.push(s); } else if (some) { score += 0.5; }
        });
        if (score > 0) hits.push({ l: l, score: score, snips: snips });
      });
      hits.sort(function (a, b) { return b.score - a.score || a.l.stage - b.l.stage; });
      var html = "", total = 0;
      hits.slice(0, 30).forEach(function (h) {
        var snips = h.snips.slice(0, 2);
        if (!snips.length) {
          snips = h.l.sentences.filter(function (s) {
            var low = s.t.toLowerCase();
            return terms.some(function (t) { return low.indexOf(t) !== -1; });
          }).slice(0, 2);
          if (!snips.length) snips = h.l.sentences.slice(0, 1);
        }
        total += Math.max(1, snips.length);
        html += '<a class="search-result" href="' + h.l.url + '">' +
          '<div class="sr-head"><span class="sr-stage">阶段 ' + h.l.stage + "</span>" +
          '<span class="sr-title">' + highlight(h.l.title, terms) + "</span></div>" +
          snips.map(function (s) {
            return '<p class="sr-snippet"><span class="kind">' + escapeHtml(s.k) + "</span>" +
              highlight(clip(s.t, terms), terms) + "</p>";
          }).join("") + "</a>";
      });
      results.innerHTML = html;
      count.textContent = hits.length ? hits.length + " 节 · 约 " + total + " 处" : "0 节";
      empty.hidden = hits.length > 0;
      try {
        var u = new URL(window.location.href);
        u.searchParams.set("q", q);
        history.replaceState(null, "", u);
      } catch (e) {}
    }
    input.addEventListener("input", function () { render(input.value); });
    var form = document.getElementById("search-form");
    if (form) form.addEventListener("submit", function (e) { e.preventDefault(); render(input.value); });
    document.querySelectorAll("[data-q]").forEach(function (b) {
      b.addEventListener("click", function () {
        input.value = b.getAttribute("data-q"); render(input.value); input.focus();
      });
    });
    var initial = "";
    try { initial = new URLSearchParams(window.location.search).get("q") || ""; } catch (e) {}
    if (initial) { input.value = initial; render(initial); } else { render(""); }
  }

  function init() {
    render(); initToc(); initReadBar(); initCatalog(); initSearch();
    window.addEventListener("storage", function (e) {
      if (e.key === KEY) { state = load(); render(); initCatalog(); }
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
