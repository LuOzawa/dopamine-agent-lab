/* DeepSeek Harness 学习手册 — 进度、目录、搜索 */
(function () {
  "use strict";

  var KEY = "dsh-handbook:v1";
  var STAGE_TOTAL = { 1: 4, 2: 6, 3: 8, 4: 4, 5: 6, 6: 5 };
  var TOTAL = Object.keys(STAGE_TOTAL).reduce(function (n, k) { return n + STAGE_TOTAL[k]; }, 0);
  var storageProblem = "";
  var state = load();

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      var obj = raw ? JSON.parse(raw) : {};
      if (!obj || typeof obj !== "object" || Array.isArray(obj)) throw new Error("Invalid progress");
      var clean = {};
      Object.keys(obj).forEach(function (id) { if (validId(id) && obj[id] === true) clean[id] = true; });
      if (validId(obj._lastRead)) clean._lastRead = obj._lastRead;
      return clean;
    } catch (e) {
      storageProblem = "无法读取已保存的学习进度；当前仅显示本次阅读状态。";
      return {};
    }
  }
  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
      storageProblem = "";
      renderStorage();
      return true;
    } catch (e) {
      storageProblem = "本次进度未保存：浏览器存储不可用或空间不足，刷新或关闭页面后可能丢失。";
      renderStorage();
      return false;
    }
  }
  function renderStorage() {
    var notice = document.querySelector("[data-storage-notice]");
    if (notice) { notice.textContent = storageProblem; notice.hidden = !storageProblem; }
    document.querySelectorAll("[data-progress-note]").forEach(function (el) {
      el.textContent = storageProblem ? "仅本次有效 · 进度未保存" : "进度保存在本机浏览器";
    });
  }
  function pct(a, b) { return b ? Math.round((a / b) * 100) : 0; }
  function validId(id) {
    var match = typeof id === "string" && id.match(/^s([1-6])-([1-9]\d*)$/);
    return !!match && Number(match[2]) <= STAGE_TOTAL[match[1]];
  }
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
    renderStorage(); renderResume();
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
      bar.style.width = pct(c, STAGE_TOTAL[n]) + "%";
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

  function renderResume() {
    var link = document.querySelector("[data-resume]");
    var data = document.getElementById("resume-lessons");
    if (!link || !data) return;
    var lessons = JSON.parse(data.textContent);
    var remaining = lessons.filter(function (lesson) { return !state[lesson.id]; });
    var started = !!state._lastRead || lessons.some(function (lesson) { return state[lesson.id]; });
    var target = remaining.find(function (lesson) { return lesson.id === state._lastRead; }) || remaining[0];
    link.href = target ? target.url : "contents.html";
    link.textContent = !target ? "全部完成 · 回顾章节" : started ? "继续阅读：" + target.num + " " + target.title : "开始阅读";
    var note = document.querySelector("[data-resume-note]");
    if (note) note.textContent = !target ? "33 节已全部完成，可从目录重新温习。" : started ? "优先返回上次未完成的小节；已完成时转到阅读顺序中首个未完成小节。" : "从第 1 节开始，也可以按下方路线选择章节。";
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-done-id]");
    if (btn) {
      var id = btn.getAttribute("data-done-id");
      state[id] = !state[id];
      if (!state[id]) delete state[id];
      var saved = save(); render();
      if (!saved) toast("本次进度未保存");
      else if (state[id]) {
        var n = Number((id.match(/^s(\d)-/) || [])[1]);
        var c = stageDone(n);
        toast(c === STAGE_TOTAL[n] ? "第 " + n + " 章全部完成" : "已标记完成 · 本章 " + c + "/" + STAGE_TOTAL[n]);
      }
      return;
    }
    var reset = e.target.closest("[data-reset]");
    if (reset && window.confirm("确定清空本机学习进度？")) {
      state = {}; var cleared = save(); render();
      toast(cleared ? "进度已清空" : "本次清空未保存，原记录可能仍在浏览器中");
    }
  });

  function initToc() {
    var links = Array.prototype.slice.call(document.querySelectorAll(".toc a[href^='#'], .mobile-toc a[href^='#']"));
    var sections = Array.prototype.slice.call(document.querySelectorAll(".lesson[id]"));
    if (!links.length || !sections.length) return;
    var mobile = document.querySelector(".mobile-toc");
    var disclosure = mobile && mobile.querySelector("details");
    var current = document.querySelector("[data-toc-current]");
    var lastActive = null;
    function activate(id) {
      links.forEach(function (a) {
        var active = a.getAttribute("href") === "#" + id;
        a.classList.toggle("active", active);
        if (active) a.setAttribute("aria-current", "location");
        else a.removeAttribute("aria-current");
        if (active && current) current.textContent = Array.prototype.map.call(a.children, function (span) { return span.textContent.trim(); }).join(" ");
      });
      if (lastActive !== id) {
        lastActive = id;
        state._lastRead = id;
        save();
      }
    }
    var pending = false;
    function update() {
      pending = false;
      var header = document.querySelector(".topbar");
      var offset = (header ? header.getBoundingClientRect().height : 0) + 24;
      if (mobile && mobile.getClientRects().length) {
        offset += mobile.querySelector("summary").getBoundingClientRect().height;
      }
      var id = sections[0].id;
      sections.forEach(function (section) {
        if (section.getBoundingClientRect().top <= offset + 1) id = section.id;
      });
      activate(id);
    }
    function schedule() {
      if (!pending) { pending = true; window.requestAnimationFrame(update); }
    }
    links.forEach(function (a) {
      a.addEventListener("click", function () {
        var id = a.getAttribute("href").slice(1);
        if (disclosure && mobile.contains(a)) {
          disclosure.open = false;
          document.getElementById(id).focus({ preventScroll: true });
        }
        activate(id);
      });
    });
    document.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    window.addEventListener("hashchange", schedule);
    window.addEventListener("pageshow", schedule);
    var initialId = window.location.hash.slice(1);
    if (sections.some(function (section) { return section.id === initialId; })) activate(initialId);
    else update();
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
      // Match plain text once; escape each fragment before adding markup.
      var words = terms.filter(Boolean).sort(function (a, b) { return b.length - a.length; });
      if (!words.length) return escapeHtml(text);
      var re = new RegExp(words.map(escapeRe).join("|"), "gi");
      var out = "", cursor = 0;
      text.replace(re, function (match, offset) {
        out += escapeHtml(text.slice(cursor, offset)) + "<mark>" + escapeHtml(match) + "</mark>";
        cursor = offset + match.length;
        return match;
      });
      return out + escapeHtml(text.slice(cursor));
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
      try {
        var u = new URL(window.location.href);
        if (q) u.searchParams.set("q", q);
        else u.searchParams.delete("q");
        history.replaceState(null, "", u);
      } catch (e) {}
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
      hits.forEach(function (h) {
        var snips = h.snips.slice(0, 2);
        if (!snips.length) {
          snips = h.l.sentences.filter(function (s) {
            var low = s.t.toLowerCase();
            return terms.some(function (t) { return low.indexOf(t) !== -1; });
          }).slice(0, 2);
          if (!snips.length) snips = h.l.sentences.slice(0, 1);
        }
        total += snips.length;
        html += '<a class="search-result" href="' + h.l.url + '">' +
          '<div class="sr-head"><span class="sr-stage">阶段 ' + h.l.stage + "</span>" +
          '<span class="sr-title">' + highlight(h.l.title, terms) + "</span></div>" +
          snips.map(function (s) {
            return '<p class="sr-snippet"><span class="kind">' + escapeHtml(s.k) + "</span>" +
              highlight(clip(s.t, terms), terms) + "</p>";
          }).join("") + "</a>";
      });
      results.innerHTML = html;
      count.textContent = hits.length ? hits.length + " 节 · 展示 " + total + " 条摘要" : "0 节";
      empty.hidden = hits.length > 0;
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

  function initCopy() {
    document.querySelectorAll("[data-copy]").forEach(function (button) {
      button.hidden = false;
      button.addEventListener("click", async function () {
        var code = document.getElementById(button.getAttribute("data-copy"));
        if (!code) return;
        button.disabled = true;
        try {
          if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error("Clipboard unavailable");
          await navigator.clipboard.writeText(code.textContent);
          toast("代码已复制");
        } catch (e) {
          var range = document.createRange();
          range.selectNodeContents(code);
          var selection = window.getSelection();
          selection.removeAllRanges(); selection.addRange(range);
          var copied = false;
          try { copied = document.execCommand("copy"); } catch (err) {}
          if (copied) { selection.removeAllRanges(); toast("代码已复制"); }
          else toast("自动复制失败，代码已选中；请按 Ctrl+C 或 ⌘C 复制");
        } finally { button.disabled = false; }
      });
    });
  }

  function init() {
    render(); initToc(); initReadBar(); initCatalog(); initSearch(); initCopy();
    window.addEventListener("storage", function (e) {
      if (e.key === KEY || e.key === null) { storageProblem = ""; state = load(); render(); initCatalog(); }
    });
    window.addEventListener("pageshow", function (e) {
      if (e.persisted) { storageProblem = ""; state = load(); render(); }
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
