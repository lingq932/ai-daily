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
