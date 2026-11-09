/* ==========================================================================
   app.js — 学习进度、目录高亮、阅读进度、轻提示
   依赖：无。数据全部存在浏览器 localStorage，不上传、不联网。
   ========================================================================== */
(function () {
  "use strict";

  var KEY = "dopa-agent-lab:v1";
  var STAGE_TOTAL = {1:4, 2:5, 3:4, 4:3, 5:7, 6:7, 7:9, 8:8};
  var TOTAL = Object.keys(STAGE_TOTAL).reduce(function (s, k) { return s + STAGE_TOTAL[k]; }, 0);

  var storageWarning = "";
  var state = load();

  function validLesson(id) {
    var m = /^s([1-8])-(\d+)$/.exec(id || "");
    return !!m && Number(m[2]) >= 1 && Number(m[2]) <= STAGE_TOTAL[m[1]];
  }

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      var obj = raw ? JSON.parse(raw) : {};
      if (!obj || typeof obj !== "object" || Array.isArray(obj)) throw new Error("invalid progress");
      var clean = {};
      Object.keys(obj).forEach(function (id) {
        if (validLesson(id) && obj[id] === true) clean[id] = true;
      });
      if (validLesson(obj._lastLesson)) clean._lastLesson = obj._lastLesson;
      return clean;
    } catch (e) {
      storageWarning = "无法读取本机学习记录。已有记录可能暂不可用，请检查浏览器的本地存储设置。";
      return {};
    }
  }

  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
      storageWarning = "";
      renderStorageWarning();
      return true;
    } catch (e) {
      storageWarning = "学习记录未能保存，当前更改仅在此页面临时有效，刷新或离开后可能丢失。请检查浏览器的本地存储设置或可用空间，再点击重试保存。";
      renderStorageWarning();
      return false;
    }
  }

  function renderStorageWarning() {
    var notice = document.getElementById("storage-notice");
    if (!notice && storageWarning) {
      notice = document.createElement("div");
      notice.id = "storage-notice";
      notice.className = "storage-notice";
      notice.setAttribute("role", "status");
      var message = document.createElement("p");
      var retry = document.createElement("button");
      retry.type = "button";
      retry.className = "btn sm";
      retry.textContent = "重试保存";
      retry.addEventListener("click", function () {
        if (save()) toast("学习记录已保存");
      });
      notice.appendChild(message);
      notice.appendChild(retry);
      var main = document.getElementById("main");
      main.insertBefore(notice, main.firstChild);
    }
    if (notice) {
      notice.hidden = !storageWarning;
      notice.querySelector("p").textContent = storageWarning;
      notice.querySelector("button").hidden = storageWarning.indexOf("未能保存") === -1;
    }
  }

  function rememberLesson(id) {
    if (!validLesson(id) || state._lastLesson === id) return;
    state._lastLesson = id;
    save();
  }

  function renderContinue() {
    var link = document.getElementById("continue-learning");
    if (!link) return;
    var lessons = window.__LESSON_MAP__ || [];
    var last = lessons.find(function (l) { return l.id === state._lastLesson; });
    var hasProgress = Object.keys(state).some(function (id) { return validLesson(id) && state[id]; });
    var next = lessons.find(function (l) { return !state[l.id]; });
    // 未完成的上次阅读优先；完成后推荐后续小节，学完末节后补齐前面遗漏。
    if (last && state[last.id]) {
      var after = lessons.slice(lessons.indexOf(last) + 1);
      next = after.find(function (l) { return !state[l.id]; }) || next;
    }
    var target = last && !state[last.id] ? last : next;
    var active = !!last || hasProgress;
    var complete = lessons.length > 0 && hasProgress && !next;
    link.href = complete ? "contents.html" : target ? target.url : "stage-1.html#s1-1";
    link.querySelector("span").textContent = complete ? "全部完成 · 回顾课程" : active ? "继续学习" : "从阶段 1 开始";
    var hint = document.getElementById("continue-hint");
    hint.hidden = !active;
    hint.textContent = complete ? "47 节已全部完成，可以回顾目录和自检题。" : target ?
      (last && !state[last.id] ? "上次读到：" : "建议下一节：") + target.id.slice(1).replace("-", ".") + " · " + target.title + " · " + target.duration : "";
  }

  function stageCount(n) {
    var ids = Object.keys(state).filter(function (id) {
      return origin(id) === "s" + n + "-" && state[id];
    });
    return Math.min(ids.length, STAGE_TOTAL[n] || 999);
  }

  function origin(id) {
    return String(id).split("-")[0] + "-";
  }

  function pct(a, b) {
    return b > 0 ? Math.round((a / b) * 100) : 0;
  }

  /* —— Toast —— */
  var toastEl = null;
  var toastTimer = null;
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
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove("show"); }, 2400);
  }

  /* —— 进度渲染 —— */
  function render() {
    /* 完成按钮 + 卡片状态 */
    var buttons = document.querySelectorAll("[data-done-id]");
    buttons.forEach(function (btn) {
      var id = btn.getAttribute("data-done-id");
      var isDone = !!state[id];
      btn.setAttribute("aria-pressed", isDone ? "true" : "false");
      btn.querySelector(".label").textContent = isDone ? "已完成" : "标记完成";
      var card = btn.closest(".lesson");
      if (card) card.classList.toggle("is-done", isDone);
    });

    /* 阶段进度条 */
    document.querySelectorAll("[data-stage-bar]").forEach(function (bar) {
      var n = Number(bar.getAttribute("data-stage-bar"));
      var c = stageCount(n);
      var total = STAGE_TOTAL[n] || 1;
      var fill = bar.matches("i") ? bar : bar.querySelector("i");
      if (fill) fill.style.width = pct(c, total) + "%";
      var label = document.querySelector('[data-stage-label="' + n + '"]');
      if (label) label.textContent = c + " / " + total;
    });

    /* 首页阶段卡片圆环 */
    document.querySelectorAll("[data-ring]").forEach(function (svg) {
      var n = Number(svg.getAttribute("data-ring"));
      var c = stageCount(n);
      var total = STAGE_TOTAL[n] || 1;
      var fg = svg.querySelector(".fg");
      var label = svg.querySelector("text");
      var r = 22;
      var cir = 2 * Math.PI * r;
      if (fg) {
        fg.style.strokeDasharray = cir;
        fg.style.strokeDashoffset = cir * (1 - c / total);
      }
      if (label) label.textContent = c + "/" + total;
      svg.setAttribute("aria-label", "阶段 " + n + "：已完成 " + c + " 节，共 " + total + " 节");
    });

    /* 顶部迷你进度 */
    var allDone = Object.keys(state).filter(function (k) { return state[k] && /^s[1-8]-\d+$/.test(k); }).length;
    document.querySelectorAll("[data-mini-bar]").forEach(function (el) {
      el.style.width = pct(Math.min(allDone, TOTAL), TOTAL) + "%";
    });
    document.querySelectorAll("[data-mini-text]").forEach(function (el) {
      el.textContent = Math.min(allDone, TOTAL) + "/" + TOTAL;
    });
    renderContinue();
  }

  /* —— 完成切换 —— */
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-done-id]");
    if (btn) {
      var id = btn.getAttribute("data-done-id");
      state[id] = !state[id];
      if (!state[id]) delete state[id];
      state._lastLesson = id;
      var saved = save();
      render();
      renderCatalog();
      if (!saved) { toast("保存失败 · 当前更改仅临时有效"); return; }
      if (state[id]) {
        var stage = Number((id.match(/^s(\d)-/) || [])[1]);
        var c = stageCount(stage);
        var total = STAGE_TOTAL[stage] || 1;
        if (c === total) toast("阶段 " + stage + " 全部完成，可以进入下一阶段了");
        else toast("已标记完成 · 阶段 " + stage + " 进度 " + c + "/" + total);
      } else toast("已取消完成标记");
      return;
    }

    var reset = e.target.closest("[data-reset]");
    if (reset) {
      if (window.confirm("确定清空本机所有学习进度？此操作不可撤销。")) {
        var previous = state;
        state = {};
        if (!save()) {
          state = previous;
          storageWarning = "未能清空本机学习记录，原记录已保留。请检查浏览器的本地存储设置或可用空间，再点击清空学习进度。";
          renderStorageWarning();
          toast("清空失败，原学习记录已保留，请稍后重试清空");
          return;
        }
        render();
        renderCatalog();
        toast("进度已清空");
      }
    }
  });


  /* —— 全文搜索（搜索页） —— */
  function initSearchPage() {
    var input = document.getElementById("search-q");
    if (!input) return;
    var data = window.__SEARCH_INDEX__;
    var resultsEl = document.getElementById("search-results");
    var countEl = document.getElementById("search-count");
    var emptyEl = document.getElementById("search-empty");
    var idleEl = document.getElementById("search-idle");
    var metaEl = document.getElementById("search-index-meta");
    var form = document.getElementById("search-form");

    if (!data || !data.lessons) {
      if (countEl) countEl.textContent = "索引未加载";
      return;
    }
    if (metaEl) {
      var totalSentences = data.lessons.reduce(function (n, l) { return n + l.sentences.length; }, 0);
      metaEl.textContent = data.count + " 节 · " + totalSentences + " 句 · 索引 " + data.generated;
    }

    function escapeHtml(str) {
      return String(str).replace(/[&<>"']/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '\"': "&quot;", "'": "&#39;" }[c];
      });
    }
    function escapeRe(str) {
      return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }
    function clip(text, terms) {
      if (text.length <= 150) return text;
      var low = text.toLowerCase(), idx = -1;
      terms.forEach(function (t) {
        var i = low.indexOf(t);
        if (i !== -1 && (idx === -1 || i < idx)) idx = i;
      });
      var start = Math.max(0, idx - 45);
      var end = Math.min(text.length, start + 170);
      if (end - start < 140) start = Math.max(0, end - 170);
      return (start > 0 ? "…" : "") + text.slice(start, end) + (end < text.length ? "…" : "");
    }
    function highlight(text, terms) {
      var words = Array.from(new Set(terms.filter(Boolean))).sort(function (a, b) { return b.length - a.length; });
      if (!words.length) return escapeHtml(text);
      var pattern = new RegExp(words.map(escapeRe).join("|"), "gi");
      var out = "", cursor = 0;
      // 仅匹配原始文本，再逐段转义，避免修改已生成的标签或 HTML 实体。
      String(text).replace(pattern, function (match, offset) {
        out += escapeHtml(text.slice(cursor, offset)) + "<mark>" + escapeHtml(match) + "</mark>";
        cursor = offset + match.length;
        return match;
      });
      return out + escapeHtml(text.slice(cursor));
    }

    function render(raw) {
      var q = (raw || "").trim();
      var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
      try {
        var url = new URL(window.location.href);
        if (q) url.searchParams.set("q", q);
        else url.searchParams.delete("q");
        history.replaceState(null, "", url);
      } catch (e) { /* 部分 file:// 浏览器禁止改 URL，搜索仍可用。 */ }
      if (!terms.length) {
        resultsEl.innerHTML = "";
        countEl.textContent = "输入关键词开始";
        emptyEl.hidden = true;
        if (idleEl) idleEl.hidden = false;
        return;
      }
      if (idleEl) idleEl.hidden = true;

      var hits = [];
      data.lessons.forEach(function (l) {
        var score = 0, snips = [];
        var title = l.title.toLowerCase();
        terms.forEach(function (t) { if (title.indexOf(t) !== -1) score += 6; });
        l.sentences.forEach(function (s) {
          var low = s.t.toLowerCase();
          var all = terms.every(function (t) { return low.indexOf(t) !== -1; });
          var some = terms.some(function (t) { return low.indexOf(t) !== -1; });
          if (all) { score += 3; snips.push(s); }
          else if (some) { score += 0.5; }
        });
        if (score > 0) hits.push({ l: l, score: score, snips: snips });
      });
      hits.sort(function (a, b) { return b.score - a.score || a.l.stage - b.l.stage; });

      var shown = hits;
      var total = 0;
      var html = "";
      shown.forEach(function (h) {
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
          '<div class="sr-head"><span class="sr-stage">阶段 ' + h.l.stage + '</span>' +
          '<span class="sr-title">' + highlight(h.l.title, terms) + "</span></div>" +
          snips.map(function (s) {
            return '<p class="sr-snippet"><span class="kind">' + escapeHtml(s.k) + "</span>" +
              highlight(clip(s.t, terms), terms) + "</p>";
          }).join("") +
          "</a>";
      });

      resultsEl.innerHTML = html;
      countEl.textContent = hits.length ? hits.length + " 节 · 展示 " + total + " 条摘要" : "0 节";
      emptyEl.hidden = hits.length > 0;
    }

    function run() { render(input.value); }

    input.addEventListener("input", run);
    var clear = document.getElementById("search-clear");
    if (clear) clear.addEventListener("click", function () {
      input.value = "";
      run();
      input.focus();
    });
    if (form) {
      form.addEventListener("submit", function (e) { e.preventDefault(); run(); });
    }
    document.querySelectorAll("[data-q]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        input.value = btn.getAttribute("data-q");
        run();
        input.focus();
      });
    });

    var initial = "";
    try { initial = new URLSearchParams(window.location.search).get("q") || ""; } catch (e) {}
    if (initial) { input.value = initial; run(); } else { render(""); }
  }

  /* —— 全部目录：完成态、分组计数、搜索 —— */
  function renderCatalog() {
    document.querySelectorAll("[data-chapter]").forEach(function (row) {
      var id = row.getAttribute("data-chapter");
      row.classList.toggle("is-done", !!state[id]);
    });
    document.querySelectorAll("[data-group-done]").forEach(function (el) {
      var g = el.getAttribute("data-group-done");
      var rows = document.querySelectorAll('[data-chapter][data-group="' + g + '"]');
      var c = 0;
      rows.forEach(function (r) { if (state[r.getAttribute("data-chapter")]) c++; });
      el.textContent = c;
    });
  }

  function initCatalogFilter() {
    var q = document.getElementById("catalog-q");
    if (!q) return;
    var rows = Array.prototype.slice.call(document.querySelectorAll(".chapter-row"));
    var groups = Array.prototype.slice.call(document.querySelectorAll(".catalog-group"));
    var count = document.getElementById("catalog-count");
    var empty = document.getElementById("catalog-empty");
    function apply() {
      var v = q.value.trim().toLowerCase();
      var n = 0;
      rows.forEach(function (r) {
        var hit = !v || r.textContent.toLowerCase().indexOf(v) !== -1;
        r.hidden = !hit;
        if (hit) n++;
      });
      groups.forEach(function (g) {
        g.hidden = !g.querySelector(".chapter-row:not([hidden])");
      });
      if (count) count.textContent = n + " 项";
      if (empty) empty.hidden = n > 0;
    }
    q.addEventListener("input", apply);
  }

  /* —— 目录高亮 —— */
  function initToc() {
    var links = Array.prototype.slice.call(document.querySelectorAll(".toc a[href^='#']"));
    if (!links.length) return;
    var disclosure = document.querySelector(".toc details");
    var current = document.querySelector(".toc-current");
    var desktop = window.matchMedia("(min-width: 1024px)");
    function adapt() { if (disclosure) disclosure.open = desktop.matches; }
    adapt();
    if (desktop.addEventListener) desktop.addEventListener("change", adapt);
    else desktop.addListener(adapt);
    var sections = links
      .map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); })
      .filter(Boolean);
    var activeId = "";
    function activate(section) {
      if (!section || activeId === section.id) return;
      activeId = section.id;
      links.forEach(function (a) {
        var active = a.getAttribute("href") === "#" + activeId;
        a.classList.toggle("active", active);
        if (active) {
          a.setAttribute("aria-current", "location");
          if (current) current.textContent = "当前：" + a.textContent;
        } else a.removeAttribute("aria-current");
      });
      rememberLesson(activeId);
    }
    links.forEach(function (a) {
      a.addEventListener("click", function (e) {
        var section = document.getElementById(a.hash.slice(1));
        if (!section) return;
        activate(section);
        if (disclosure && !desktop.matches) {
          e.preventDefault();
          disclosure.open = false;
          window.location.hash = section.id;
          requestAnimationFrame(function () {
            section.setAttribute("tabindex", "-1");
            section.focus({ preventScroll: true });
            section.scrollIntoView({ block: "start", behavior: "instant" });
          });
        }
      });
    });
    var pending = false;
    function update() {
      pending = false;
      var topbar = document.querySelector(".topbar");
      var offset = (topbar ? topbar.getBoundingClientRect().height : 68) + (desktop.matches ? 40 : 110);
      var chosen = null;
      sections.forEach(function (s) {
        var rect = s.getBoundingClientRect();
        if (rect.top <= offset && rect.bottom > offset) chosen = s;
      });
      if (!chosen) chosen = sections.find(function (s) {
        var rect = s.getBoundingClientRect();
        return rect.top >= offset && rect.top < window.innerHeight * 0.85;
      });
      activate(chosen);
    }
    function schedule() {
      if (!pending) { pending = true; requestAnimationFrame(update); }
    }
    var initial = sections.find(function (s) { return "#" + s.id === window.location.hash; });
    activate(initial);
    document.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    window.addEventListener("hashchange", function () {
      activate(sections.find(function (s) { return "#" + s.id === window.location.hash; }));
    });
    schedule();
  }

  /* —— 阅读进度条 —— */
  function initReadBar() {
    var bar = document.querySelector(".read-progress");
    if (!bar) return;
    function update() {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
    }
    document.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  /* —— 初始化与跨页面记录同步 —— */
  function init() {
    var header = document.querySelector(".topbar");
    function measureHeader() {
      if (header) document.documentElement.style.setProperty("--header-offset", Math.ceil(header.getBoundingClientRect().height) + "px");
    }
    measureHeader();
    window.addEventListener("resize", measureHeader);
    if (header && "ResizeObserver" in window) new window.ResizeObserver(measureHeader).observe(header);
    renderStorageWarning();
    render();
    renderCatalog();
    initCatalogFilter();
    initSearchPage();
    initToc();
    initReadBar();
    /* 跨标签页同步 */
    window.addEventListener("storage", function (e) {
      if (e.key === KEY || e.key === null) { state = load(); render(); renderCatalog(); renderStorageWarning(); }
    });
    window.addEventListener("pageshow", function (e) {
      if (e.persisted && !storageWarning) { state = load(); render(); renderCatalog(); renderStorageWarning(); }
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
