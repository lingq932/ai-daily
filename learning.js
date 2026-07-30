/* 工程解码（第四版）——独立学习页
 * 负责：视图 tab 切换 + 加载 learning.json + 卡片渲染 + 主题筛 + 搜索 + 往期归档折叠
 * 完全独立于 app.js，不触碰现有 11 板块逻辑。
 */
(function () {
  const RECENT_LIMIT = 50; // 默认主列表最多显示最新 50 条，其余进往期归档

  const catClass = {
    "技术实现": "impl",
    "技术边界": "boundary",
    "vibe coding 企业闭环": "loop",
  };

  let allItems = [];
  let curCat = "all";
  let curKeyword = "";
  let archiveOpen = false;
  let loaded = false;

  // ========== 视图切换 ==========
  function initTabs() {
    const tabs = document.querySelectorAll(".view-tab");
    const reportView = document.getElementById("reportView");
    const decodeView = document.getElementById("decodeView");
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        tabs.forEach(t => t.classList.remove("active"));
        this.classList.add("active");
        if (this.dataset.view === "decode") {
          reportView.style.display = "none";
          decodeView.style.display = "block";
          if (!loaded) loadLearning();
        } else {
          decodeView.style.display = "none";
          reportView.style.display = "flex"; // .main-layout 原本是 flex
        }
        window.scrollTo({ top: 0 });
      });
    });
  }

  // ========== 加载数据 ==========
  async function loadLearning() {
    loaded = true;
    try {
      const resp = await fetch("data/learning.json");
      if (!resp.ok) throw new Error("no learning data");
      const data = await resp.json();
      allItems = (data.items || []).slice()
        .sort((a, b) => (b.date || "").localeCompare(a.date || ""));
    } catch (e) {
      allItems = [];
    }
    render();
  }

  // ========== 过滤 ==========
  function filtered() {
    return allItems.filter(function (it) {
      if (curCat !== "all" && it.category !== curCat) return false;
      if (curKeyword) {
        const blob = [it.title, it.whatIsIt, it.boundary, it.whyLearn, it.source, it.category]
          .join(" ").toLowerCase();
        if (!blob.includes(curKeyword)) return false;
      }
      return true;
    });
  }

  // ========== 渲染 ==========
  function render() {
    const list = document.getElementById("decodeList");
    const archiveList = document.getElementById("decodeArchiveList");
    const archiveToggle = document.getElementById("decodeArchiveToggle");
    const archiveCount = document.getElementById("decodeArchiveCount");
    const archiveBtn = document.getElementById("decodeArchiveBtn");
    const empty = document.getElementById("decodeEmpty");
    const countEl = document.getElementById("decodeCount");

    const items = filtered();
    list.innerHTML = "";
    archiveList.innerHTML = "";

    if (items.length === 0) {
      empty.style.display = "block";
      archiveToggle.style.display = "none";
      archiveList.style.display = "none";
      countEl.textContent = "";
      return;
    }
    empty.style.display = "none";

    const isDefault = (curCat === "all" && !curKeyword);
    countEl.textContent = "共 " + items.length + " 条" + (isDefault ? "" : "（筛选后）");

    let recent = items, archive = [];
    if (isDefault && items.length > RECENT_LIMIT) {
      recent = items.slice(0, RECENT_LIMIT);
      archive = items.slice(RECENT_LIMIT);
    }

    recent.forEach(it => list.appendChild(card(it)));

    if (archive.length > 0) {
      archiveToggle.style.display = "block";
      archiveCount.textContent = archive.length;
      archive.forEach(it => archiveList.appendChild(card(it)));
      archiveList.style.display = archiveOpen ? "flex" : "none";
      archiveBtn.textContent = archiveOpen
        ? "收起往期归档"
        : "展开往期归档（" + archive.length + " 条）";
    } else {
      archiveToggle.style.display = "none";
      archiveList.style.display = "none";
    }
  }

  function seg(label, text, extraClass) {
    if (!text) return "";
    return '<div class="decode-seg ' + (extraClass || "") + '">' +
      '<span class="decode-seg-label">' + label + '</span>' +
      '<p>' + esc(text) + '</p></div>';
  }

  function card(it) {
    const el = document.createElement("article");
    el.className = "decode-card";
    const cls = catClass[it.category] || "impl";
    const dateShort = (it.date || "").slice(5); // MM-DD
    el.innerHTML =
      '<div class="decode-card-top">' +
        '<span class="decode-cat decode-cat--' + cls + '">' + esc(it.category) + '</span>' +
        '<span class="decode-card-date">' + esc(dateShort) + '</span>' +
      '</div>' +
      '<h3 class="decode-card-title">' + esc(it.title) + '</h3>' +
      seg("讲了什么", it.whatIsIt) +
      seg("技术边界", it.boundary, "decode-seg--boundary") +
      seg("为什么值得你学", it.whyLearn) +
      '<div class="decode-card-foot">' +
        '<span class="decode-src">来源 · ' + esc(it.source) + '</span>' +
        (it.url ? '<a href="' + esc(it.url) + '" target="_blank" rel="noopener">查看原文 ↗</a>' : '') +
      '</div>';
    return el;
  }

  function esc(s) {
    if (!s) return "";
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  // ========== 控件事件 ==========
  function initControls() {
    document.querySelectorAll(".decode-chip").forEach(function (chip) {
      chip.addEventListener("click", function () {
        document.querySelectorAll(".decode-chip").forEach(c => c.classList.remove("active"));
        this.classList.add("active");
        curCat = this.dataset.cat;
        archiveOpen = false;
        render();
      });
    });

    document.getElementById("decodeSearch").addEventListener("input", function () {
      curKeyword = this.value.trim().toLowerCase();
      archiveOpen = false;
      render();
    });

    document.getElementById("decodeArchiveBtn").addEventListener("click", function () {
      archiveOpen = !archiveOpen;
      render();
    });
  }

  initTabs();
  initControls();
})();

/* ========== 最佳实践子区（独立 IIFE，不触碰上面的三主题卡片流）==========
 * 加载 data/best_practices.json，两个视角「按场景 / 按技术」切换，
 * 同视角内按 label 分组展示，卡片渲染四段：是什么 / 怎么做 / 常见的坑 / 案例来源。
 */
(function () {
  let bpItems = [];
  let bpView = "场景";
  let bpLoaded = false;

  function esc(s) {
    if (!s) return "";
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  async function loadBP() {
    bpLoaded = true;
    try {
      const resp = await fetch("data/best_practices.json");
      if (!resp.ok) throw new Error("no bp data");
      const data = await resp.json();
      bpItems = (data.items || []).slice()
        .sort((a, b) => (b.date || "").localeCompare(a.date || ""));
    } catch (e) {
      bpItems = [];
    }
    renderBP();
  }

  function renderBP() {
    const list = document.getElementById("bpList");
    const empty = document.getElementById("bpEmpty");
    if (!list) return;
    list.innerHTML = "";

    const items = bpItems.filter(it => (it.viewType || "场景") === bpView);
    if (items.length === 0) {
      empty.style.display = "block";
      return;
    }
    empty.style.display = "none";

    // 同视角内按 label 分组
    const groups = {};
    const order = [];
    items.forEach(function (it) {
      const key = it.label || "其他";
      if (!groups[key]) { groups[key] = []; order.push(key); }
      groups[key].push(it);
    });

    order.forEach(function (label) {
      const groupEl = document.createElement("div");
      groupEl.className = "bp-group";
      groupEl.innerHTML = '<div class="bp-group-label">' +
        '<span class="bp-group-type">' + esc(bpView) + '</span>' +
        '<span class="bp-group-name">' + esc(label) + '</span></div>';
      groups[label].forEach(it => groupEl.appendChild(bpCard(it)));
      list.appendChild(groupEl);
    });
  }

  function bpCard(it) {
    const el = document.createElement("article");
    el.className = "bp-card";
    const w = it.whatIsIt || {};
    const h = it.howTo || {};
    const keyMoves = Array.isArray(h.keyMoves) ? h.keyMoves : [];
    const cases = Array.isArray(it.cases) ? it.cases : [];
    const dateShort = (it.date || "").slice(5);

    let html =
      '<div class="bp-card-top">' +
        '<span class="bp-tag">' + esc(it.viewType || "场景") + ' · ' + esc(it.label || "") + '</span>' +
        '<span class="bp-card-date">' + esc(dateShort) + '</span>' +
      '</div>' +
      '<h4 class="bp-card-title">' + esc(it.title) + '</h4>';

    // 是什么
    let whatRows = "";
    if (w.scenario) whatRows += '<p><b>场景</b>' + esc(w.scenario) + '</p>';
    if (w.users) whatRows += '<p><b>用户群</b>' + esc(w.users) + '</p>';
    if (w.painpoint) whatRows += '<p><b>痛点</b>' + esc(w.painpoint) + '</p>';
    if (whatRows) {
      html += '<div class="bp-seg"><span class="bp-seg-label">是什么</span>' +
        '<div class="bp-what">' + whatRows + '</div></div>';
    }

    // 怎么做：架构链路 + 关键做法
    let howInner = "";
    if (h.architecture) {
      howInner += '<div class="bp-arch"><span class="bp-arch-label">架构链路</span>' +
        '<p>' + esc(h.architecture) + '</p></div>';
    }
    if (keyMoves.length) {
      howInner += '<div class="bp-moves"><span class="bp-moves-label">关键做法</span><ul>' +
        keyMoves.map(m => '<li>' + esc(m) + '</li>').join("") + '</ul></div>';
    }
    if (howInner) {
      html += '<div class="bp-seg"><span class="bp-seg-label">怎么做</span>' + howInner + '</div>';
    }

    // 常见的坑
    if (it.pitfalls) {
      html += '<div class="bp-seg bp-seg--pit"><span class="bp-seg-label">常见的坑</span>' +
        '<p>' + esc(it.pitfalls) + '</p></div>';
    }

    // 案例来源
    if (cases.length) {
      const links = cases.map(function (c) {
        const name = esc(c.source || "来源");
        return c.url
          ? '<a href="' + esc(c.url) + '" target="_blank" rel="noopener">' + name + ' ↗</a>'
          : '<span>' + name + '</span>';
      }).join("");
      html += '<div class="bp-card-foot"><span class="bp-foot-label">案例来源</span>' + links + '</div>';
    }

    el.innerHTML = html;
    return el;
  }

  function initBP() {
    const tabs = document.querySelectorAll(".bp-view-tab");
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        tabs.forEach(t => t.classList.remove("active"));
        this.classList.add("active");
        bpView = this.dataset.bpview;
        renderBP();
      });
    });

    // 用户切到「工程解码」视图时再懒加载
    document.querySelectorAll(".view-tab").forEach(function (t) {
      t.addEventListener("click", function () {
        if (this.dataset.view === "decode" && !bpLoaded) loadBP();
      });
    });
  }

  initBP();
})();
